from mpi4py import MPI
from mpi.master_slave import Master, Slave
import time

class MyApp():

    def __init__(self, slaves):
        self.master = Master(slaves)

    def terminate_slaves(self):
        """
        Call this to make all slaves exit
        """
        self.master.terminate()

    def run(self, times=100, sleep=0.3):
        """
        This is the core of my application, keep starting slaves
        as long as there is work to do
        """

        for i in range(times): # let's pretend we have stuff to do

            #
            # give work to do to each idle slave
            #
            for slave in self.master.get_avaliable():
                print('Slave %d ready to do some more work' % slave)
                data = ('Do something, my slave', 'Fix me a coffee')
                self.master.run(slave, data)

            #
            # reclaim slaves that have finished working
            # so that we can assign them more work
            #
            for slave in self.master.get_completed():
                done, message = self.master.get_data(slave)
                if done:
                    print("Slave %d finished is task and says %s" % (slave, message) )
                else:
                    print("Slave %d failed to accomplish his task" % slave)

            # sleep some time
            time.sleep(sleep)


class MySlave(Slave):

    def __init__(self):
        super(MySlave, self).__init__()

    def do_work(self, data):
        rank = MPI.COMM_WORLD.Get_rank()
        name = MPI.Get_processor_name()
        task, task_arg = data
        print('  Slave %s rank %d: task %s arg %s)' % (name, rank, task, task_arg) )
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
