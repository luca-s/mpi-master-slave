from mpi4py import MPI
from mpi.master_slave import Master, Slave
import time

class MyApp():
    """
    This is my application that has a lot of work to do
    so it gives work to do to its slaves until all the
    work is done
    """

    def __init__(self, slaves):
        # when creating the Master we tell it what slaves it can handle
        self.master = Master(slaves)

    def terminate_slaves(self):
        """
        Call this to make all slaves exit
        """
        self.master.terminate_slaves()

    def run(self, times=100, sleep=0.3):
        """
        This is the core of my application, keep starting slaves
        as long as there is work to do
        """

        for i in range(times): # let's pretend we have stuff to do

            #
            # give work to do to each idle slave
            #
            for slave in self.master.get_ready_slaves():
                print('Slave %d is going to do some more work' % slave)
                data = ('Do this', 'task details')
                self.master.run(slave, data)

            #
            # reclaim slaves that have finished working
            # so that we can assign them more work
            #
            for slave in self.master.get_completed_slaves():
                done, message = self.master.get_data(slave)
                if done:
                    print('Slave %d finished is task and says "%s"' % (slave, message) )
                else:
                    print('Slave %d failed to accomplish his task' % slave)

            # sleep some time
            time.sleep(sleep)


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
        print('  Slave %s rank %d executing "%s" with "%s"' % (name, rank, task, task_arg) )
        return (True, 'I completed my task')


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
