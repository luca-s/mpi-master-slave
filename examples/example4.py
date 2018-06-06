from mpi4py import MPI
from mpi_master_slave import Master, Slave
from mpi_master_slave import WorkQueue
from enum import IntEnum
import random
import time

Tasks = IntEnum('Tasks', 'TASK1 TASK2 TASK3')

class MyApp(object):
    """
    This is my application that has a lot of work to do so it gives work to do
    to its slaves until all the work is done. There different type of work so
    the slaves must be able to do different tasks
    """

    def __init__(self, slaves):
        # when creating the Master we tell it what slaves it can handle
        self.master = Master(slaves)
        # WorkQueue is a convenient class that run slaves on a tasks queue
        self.work_queue = WorkQueue(self.master)

    def terminate_slaves(self):
        """
        Call this to make all slaves exit their run loop
        """
        self.master.terminate_slaves()

    def __add_next_task(self, i, task=None):
        """
        we create random tasks 1-3 and add it to the work queue
        Every task has specific arguments
        """
        if task is None:
            task = random.randint(1,3)

        if task == 1:
            args = i
            data = (Tasks.TASK1, args)
        elif task == 2:
            args = (i, i*2)
            data = (Tasks.TASK2, args)
        elif task == 3:
            args = (i, 999, 'something')
            data = (Tasks.TASK3, args)

        self.work_queue.add_work(data)

    def run(self, tasks=100):
        """
        This is the core of my application, keep starting slaves
        as long as there is work to do
        """

        #
        # let's prepare our work queue. This can be built at initialization time
        # but it can also be added later as more work become available
        #
        for i in range(tasks):
            self.__add_next_task(i)
       
        #
        # Keeep starting slaves as long as there is work to do
        #
        while not self.work_queue.done():

            #
            # give more work to do to each idle slave (if any)
            #
            self.work_queue.do_work()

            #
            # reclaim returned data from completed slaves
            #
            for slave_return_data in self.work_queue.get_completed_work():
                #
                # each task type has its own return type
                #
                task, data = slave_return_data
                if task == Tasks.TASK1:
                    done, arg1 = data
                elif task == Tasks.TASK2:
                    done, arg1, arg2, arg3 = data
                elif task == Tasks.TASK3:
                    done, arg1, arg2 = data    
                if done:
                    print('Master: slave finished is task returning: %s)' % str(data))

            # sleep some time
            time.sleep(0.3)


class MySlave(Slave):
    """
    A slave process extends Slave class, overrides the 'do_work' method
    and calls 'Slave.run'. The Master will do the rest

    In this example we have different tasks but instead of creating a Slave for
    each type of taks we create only one class that can handle any type of work.
    This avoids having idle processes if, at certain times of the execution, there
    is only a particular type of work to do but the Master doesn't have the right
    slave for that task.
    """

    def __init__(self):
        super(MySlave, self).__init__()

    def do_work(self, args):
        
        # the data contains the task type
        task, data = args

        rank = MPI.COMM_WORLD.Get_rank()
        name = MPI.Get_processor_name()

        #
        # Every task type has its specific data input and return output
        #
        ret = None
        if task == Tasks.TASK1:

            arg1 = data
            print('  Slave %s rank %d executing %s with task_id %d' % (name, rank, task, arg1) )
            ret = (True, arg1)

        elif task == Tasks.TASK2:

            arg1, arg2 = data
            print('  Slave %s rank %d executing %s with task_id %d arg2 %d' % (name, rank, task, arg1, arg2) )
            ret = (True, arg1, 'something', 'else')

        elif task == Tasks.TASK3:

            arg1, arg2, arg3 = data
            print('  Slave %s rank %d executing %s with task_id %d arg2 %d arg3 %s' % (name, rank, task, arg1, arg2, arg3) )
            ret = (True, arg1, 'something')

        return (task, ret)



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
