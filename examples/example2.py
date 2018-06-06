from mpi4py import MPI
from mpi_master_slave import Master, Slave
import time

class MyApp(object):
    """
    This is my application that has a lot of work to do so it gives work to do
    to its slaves until all the work is done
    """

    def __init__(self, slaves):
        # when creating the Master we tell it what slaves it can handle
        self.master = Master(slaves)

    def terminate_slaves(self):
        """
        Call this to make all slaves exit their run loop
        """
        self.master.terminate_slaves()

    def run(self, tasks=10):
        """
        This is the core of my application, keep starting slaves
        as long as there is work to do
        """
        
        work_queue = [i for i in range(tasks)] # let's pretend this is our work queue
        
        #
        # while we have work to do and not all slaves completed
        #
        while work_queue or not self.master.done():

            #
            # give work to do to each idle slave
            #
            for slave in self.master.get_ready_slaves():
                
                if not work_queue:
                    break
                task = work_queue.pop(0) # get next task in the queue

                print('Master: slave %d is going to do task %d' % (slave, task) )
                self.master.run(slave, data=('Do task', task) )

            #
            # reclaim slaves that have finished working
            # so that we can assign them more work
            #
            for slave in self.master.get_completed_slaves():
                done, message = self.master.get_data(slave)
                if done:
                    print('Master: slave %d finished is task and says "%s"' % (slave, message) )
                else:
                    print('Master: slave %d failed to accomplish his task' % slave)

            # sleep some time
            time.sleep(0.3)


class MySlave(Slave):
    """
    A slave process extends Slave class, overrides the 'do_work' method
    and calls 'Slave.run'. The Master will do the rest
    """

    def __init__(self):
        super(MySlave, self).__init__()

    def do_work(self, data):
        rank = MPI.COMM_WORLD.Get_rank()
        name = MPI.Get_processor_name()
        task, task_arg = data
        print('  Slave %s rank %d executing "%s" task_id "%d"' % (name, rank, task, task_arg) )
        return (True, 'I completed my task (%d)' % task_arg)


def main():

    name = MPI.Get_processor_name()
    rank = MPI.COMM_WORLD.Get_rank()
    size = MPI.COMM_WORLD.Get_size()

    print('I am  %s rank %d (total %d)' % (name, rank, size) )

    if rank == 0: # Master

        app = MyApp(slaves=range(1, size))
        app.run()
        app.terminate_slaves()

    else: # Any slave

        MySlave().run()

    print('Task completed (rank %d)' % (rank) )

if __name__ == "__main__":
    main()
