from mpi4py import MPI
from mpi_master_slave import Master, Slave
from mpi_master_slave import MultiWorkQueue
from enum import IntEnum
import random
import time

Tasks = IntEnum('Tasks', 'TASK1 TASK2 TASK3')


class MyMaster(Master):
    """
    This Master class handles a specific task
    """

    def __init__(self, task, slaves = None):
        super(MyMaster, self).__init__(slaves)
        self.task = task

    def run(self, slave, data):
        args = (self.task, data)
        super(MyMaster, self).run(slave, args)

    def get_data(self, completed_slave):
        task, data = super(MyMaster, self).get_data(completed_slave)
        return data


class MyApp(object):
    """
    This is my application that has a lot of work to do so it gives work to do
    to its slaves until all the work is done. There different type of work so
    the slaves must be able to do different tasks.
    Also want to limit the number of slaves reserved to one or more tasks. We
    make use of the MultiWorkQueue class that handles multiple Masters and where
    each Master can have an optional limits on the number of slaves.
    MultiWorkQueue moves slaves between Masters when some of them are idles and
    gives slaves back when the Masters have work again.
    """

    def __init__(self, slaves,  task1_num_slave=None, task2_num_slave=None, task3_num_slave=None):
        """
        Each task/master can be limited on the number of slaves by the init
        arguments. Leave them None if you don't want to limit a specific Master
        """
        #
        # create a Master for each task
        #
        self.master1 = MyMaster(task=Tasks.TASK1)
        self.master2 = MyMaster(task=Tasks.TASK2)
        self.master3 = MyMaster(task=Tasks.TASK3)

        #
        # MultiWorkQueue is a convenient class that run multiple work queues
        # Each task needs a Tuple  with (someID, Master, None or max slaves)
        #
        masters_details = [(Tasks.TASK1, self.master1, task1_num_slave),
                           (Tasks.TASK2, self.master2, task2_num_slave),
                           (Tasks.TASK3, self.master3, task3_num_slave) ]
        self.work_queue = MultiWorkQueue(slaves, masters_details)


    def terminate_slaves(self):
        """
        Call this to make all slaves exit their run loop
        """
        self.master1.terminate_slaves()
        self.master2.terminate_slaves()
        self.master3.terminate_slaves()

    def __add_next_task(self, i, task=None):
        """
        Create random tasks 1-3 and add it to the right work queue
        """
        if task is None:
            task = random.randint(1,3)

        if task == 1:
            args = i
            self.work_queue.add_work(Tasks.TASK1, args)
        elif task == 2:
            args = (i, i*2)
            self.work_queue.add_work(Tasks.TASK2, args)
        elif task == 3:
            args = (i, 999, 'something')
            self.work_queue.add_work(Tasks.TASK3, args)

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
            for data in self.work_queue.get_completed_work(Tasks.TASK1):
                done, arg1 = data
                if done:
                    print('Master: slave finished his task returning: %s)' % str(data))

            for data in self.work_queue.get_completed_work(Tasks.TASK2):
                done, arg1, arg2, arg3 = data
                if done:
                    print('Master: slave finished his task returning: %s)' % str(data))

            for data in self.work_queue.get_completed_work(Tasks.TASK3):
                done, arg1, arg2 = data
                if done:
                    print('Master: slave finished his task returning: %s)' % str(data))

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

        app = MyApp(slaves=range(1, size), task1_num_slave=2, task2_num_slave=None, task3_num_slave=1)
        app.run()
        app.terminate_slaves()

    else: # Any slave

        MySlave().run()

    print('Task completed (rank %d)' % (rank) )

if __name__ == "__main__":
    main()
