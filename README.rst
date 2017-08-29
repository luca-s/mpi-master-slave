mpi-master-slave: Easy to use mpi master slave code using mpi4py
================================================================

Why mpi4py?
-----------

Python is such a nice and features rich language that writing the high level logic of your application with it require so little effort. Also, considering that you can wrap C or Fortran functions in Python, there is no need to write your whole application in a low level language that makes hard to change application logic, refactoring, maintenance, porting and adding new features.  Instead you can write the application in Python and cpossibly write in C/Fortran the functions that are computational expensive. There is no need to write the whole application in C/Fortran if 90% of the execution time is spent in a bunch of functions. Just focus on optimizing those functions.

Writing you application
-----------------------

`Example 1 <https://github.com/luca-s/mpi-master-slave/blob/master/example1.py>`__

Writing a master slave application is as simple as extenging Slave class and implementing the 'do_work' method and creating a Master object that controls the slaves. In this example we use WorkQueue too, a convenient class that keeps running slaves until the work queue is completed.


.. code:: python

    from mpi4py import MPI
    from mpi.master_slave import Master, Slave
    from mpi.work_queue import WorkQueue
    import time

    class MyApp(object):
        """
        This is my application that has a lot of work to do so it gives work to do
        to its slaves until all the work is done.
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

        def run(self, tasks=10):
            """
            This is the core of my application, keep starting slaves
            as long as there is work to do
            """
            
            # let's pretend this is our work queue
            for i in range(tasks):
                # 'data' will be passed to the slave
                self.work_queue.add_work(data=('Do task', i))
           
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
                    done, message = slave_return_data
                    if done:
                        print('Slave finished is task and says "%s"' % message)

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
            print('  Slave %s rank %d executing "%s" with "%d"' % (name, rank, task, task_arg) )
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


`Example 2 <https://github.com/luca-s/mpi-master-slave/blob/master/example2.py>`__

To have a better understanding on how the Master works, here is the same code above without the WorkQueue class


.. code:: python

    class MyApp(object):
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

                    print('Slave %d is going to do task %d' % (slave, task) )
                    self.master.run(slave, data=('Do task', task) )

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
                time.sleep(0.3)



Running the application
-----------------------

::

    mpiexec -n 4 python example1.py


Output:

::

    I am  lucasca-desktop rank 1 (total 4)
    I am  lucasca-desktop rank 2 (total 4)
    I am  lucasca-desktop rank 0 (total 4)
    I am  lucasca-desktop rank 3 (total 4)
    Master: slave 2 is going to do task 0
    Master: slave 3 is going to do task 1
      Slave lucasca-desktop rank 3 executing "Do task" with "1"
      Slave lucasca-desktop rank 2 executing "Do task" with "0"
    Master: slave 1 is going to do task 2
    Master: slave 2 finished is task and says "I completed my task (0)"
    Master: slave 3 finished is task and says "I completed my task (1)"
      Slave lucasca-desktop rank 1 executing "Do task" with "2"
      Slave lucasca-desktop rank 3 executing "Do task" with "4"
    Master: slave 2 is going to do task 3
    Master: slave 3 is going to do task 4
      Slave lucasca-desktop rank 2 executing "Do task" with "3"
    Master: slave 1 finished is task and says "I completed my task (2)"
    Master: slave 3 finished is task and says "I completed my task (4)"
    Master: slave 1 is going to do task 5
    Master: slave 3 is going to do task 6
      Slave lucasca-desktop rank 1 executing "Do task" with "5"
    Master: slave 2 finished is task and says "I completed my task (3)"
      Slave lucasca-desktop rank 3 executing "Do task" with "6"
    Master: slave 2 is going to do task 7
    Master: slave 1 finished is task and says "I completed my task (5)"
      Slave lucasca-desktop rank 2 executing "Do task" with "7"
    Master: slave 3 finished is task and says "I completed my task (6)"
    Master: slave 1 is going to do task 8
    Master: slave 3 is going to do task 9
    Master: slave 2 finished is task and says "I completed my task (7)"
      Slave lucasca-desktop rank 1 executing "Do task" with "8"
      Slave lucasca-desktop rank 3 executing "Do task" with "9"
    Master: slave 3 finished is task and says "I completed my task (9)"
    Master: slave 1 finished is task and says "I completed my task (8)"
    Task completed (rank 2)
    Task completed (rank 0)
    Task completed (rank 3)
    Task completed (rank 1)



Debugging
---------

We'll open a xterm terminal for each mpi process so that we can debug each process independently:

::
 
    mpiexec -n 4 xterm -e "python example1.py ; bash"


"bash" is optional - it ensures that the xterm windows will stay open; even if finished


Option 1: if you want the debugger to stop at a specific position in the code then add the following at the line where you want the debugger to stop:

::

    import ipdb; ipdb.set_trace()


Then run the application as above.


Option 2: start the debugger right after each process has started

::

    mpiexec -n 4 xterm -e "python -m pdb example1.py ; bash"


Profiling
---------

Eventually you'll probably like to profile your code to understand if there are bottlenecks. To do that you have to first include the profiling module and create one profiler object somewhere in the code


.. code:: python

    import cProfile

    pr = cProfile.Profile()


Then you have to start the profiler just before the part of the code you like to profile (you can also start/stop the profiler in different part of the code).
Once you want to see the results (or partial results) stop the profiler and print statistics.

.. code:: python

    pr.enable()

    [...code to be profiled here...]

    pr.disable()

    pr.print_stats(sort='tottime')
    pr.print_stats(sort='cumtime')


For example let's say we like to profile the Master process in the example above 

.. code:: python

    import cProfile

    [...]

        if rank == 0: # Master

            pr = cProfile.Profile()
            pr.enable()

            app = MyApp(slaves=range(1, size))
            app.run()
            app.terminate_slaves()

            pr.disable()
            pr.print_stats(sort='tottime')
            pr.print_stats(sort='cumtime')

        else: # Any slave
    [...]


Output:

::

   Ordered by: internal time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      100   30.030    0.300   30.030    0.300 {built-in method time.sleep}
      240    0.008    0.000    0.008    0.000 {built-in method builtins.print}
      221    0.003    0.000    0.004    0.000 master_slave.py:52(get_avaliable)
        1    0.002    0.002   30.049   30.049 example2.py:24(run)
      532    0.002    0.000    0.002    0.000 {method 'Iprobe' of 'mpi4py.MPI.Comm' objects}
      219    0.001    0.000    0.003    0.000 master_slave.py:74(get_completed)
      121    0.001    0.000    0.001    0.000 {method 'send' of 'mpi4py.MPI.Comm' objects}
      242    0.001    0.000    0.001    0.000 {method 'recv' of 'mpi4py.MPI.Comm' objects}
      121    0.001    0.000    0.003    0.000 master_slave.py:66(run)
      119    0.000    0.000    0.001    0.000 master_slave.py:87(get_data)
      440    0.000    0.000    0.000    0.000 {method 'keys' of 'dict' objects}
      243    0.000    0.000    0.000    0.000 {method 'add' of 'set' objects}
      241    0.000    0.000    0.000    0.000 {method 'remove' of 'set' objects}
      242    0.000    0.000    0.000    0.000 {method 'Get_source' of 'mpi4py.MPI.Status' objects}
        1    0.000    0.000    0.000    0.000 master_slave.py:12(__init__)
        1    0.000    0.000    0.000    0.000 example2.py:14(__init__)
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}


         3085 function calls in 30.049 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.002    0.002   30.049   30.049 example2.py:24(run)
      100   30.030    0.300   30.030    0.300 {built-in method time.sleep}
      240    0.008    0.000    0.008    0.000 {built-in method builtins.print}
      221    0.003    0.000    0.004    0.000 master_slave.py:52(get_avaliable)
      219    0.001    0.000    0.003    0.000 master_slave.py:74(get_completed)
      121    0.001    0.000    0.003    0.000 master_slave.py:66(run)
      532    0.002    0.000    0.002    0.000 {method 'Iprobe' of 'mpi4py.MPI.Comm' objects}
      121    0.001    0.000    0.001    0.000 {method 'send' of 'mpi4py.MPI.Comm' objects}
      242    0.001    0.000    0.001    0.000 {method 'recv' of 'mpi4py.MPI.Comm' objects}
      119    0.000    0.000    0.001    0.000 master_slave.py:87(get_data)
      440    0.000    0.000    0.000    0.000 {method 'keys' of 'dict' objects}
      243    0.000    0.000    0.000    0.000 {method 'add' of 'set' objects}
      241    0.000    0.000    0.000    0.000 {method 'remove' of 'set' objects}
      242    0.000    0.000    0.000    0.000 {method 'Get_source' of 'mpi4py.MPI.Status' objects}
        1    0.000    0.000    0.000    0.000 example2.py:14(__init__)
        1    0.000    0.000    0.000    0.000 master_slave.py:12(__init__)
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}


From the output above we can see most of the Master time is spent in time.sleep and this is good as the Master doesn't have to be busy as its role is to control the slaves.


More examples covering common scenarios
---------------------------------------

In `Example 3 <https://github.com/luca-s/mpi-master-slave/blob/master/example3.py>`__ we can see how to the slaves can handle multiple type of tasks. 

.. code:: python

    Tasks = IntEnum('Tasks', 'TASK1 TASK2 TASK3')


Instead of extending a Slave class for each type of task we have, we create only one class that can handle any type of work. This avoids having idle processes if, at certain times of the execution, there is only a particular type of work to do but the Master doesn't have the right slave for that task. If any slave can do any job, there is always a slave that can perform that task.

.. code:: python

    class MySlave(Slave):

        def __init__(self):
            super(MySlave, self).__init__()

        def do_work(self, args):
    
            # the data contains the task type
            task, data = args

            #
            # Every task type has its specific data input and return output
            #
            ret = None
            if task == Tasks.TASK1:

                arg1 = data
                [... do something...]
                ret = (True, arg1)

            elif task == Tasks.TASK2:

                arg1, arg2 = data
                [... do something...]
                ret = (True, 'All done')

            elif task == Tasks.TASK3:

                arg1, arg2, arg3 = data
                [... do something...]
                ret = (True, arg1+arg2, arg3)

            return (task, ret)


The master simply passes the task type to the slave together with the task specific data.

.. code:: python

    class MyApp(object):

        [...]

        def run(self, tasks=100):

            #
            # let's prepare our work queue. This can be built at initialization time
            # but it can also be added later as more work become available
            #
            for i in range(tasks):
                data = self.__get_next_task(i)
                self.work_queue.add_work(data)
           
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

        def __get_next_task(self, i):
            #
            # we create random tasks 1-3, every task has its own arguments
            #
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
            return data

Ourput

::

    $ mpiexec -n 16 python3 example3.py

    I am  lucasca-desktop rank 9 (total 16)
    I am  lucasca-desktop rank 12 (total 16)
    I am  lucasca-desktop rank 10 (total 16)
    I am  lucasca-desktop rank 2 (total 16)
    I am  lucasca-desktop rank 8 (total 16)
    I am  lucasca-desktop rank 14 (total 16)
    I am  lucasca-desktop rank 6 (total 16)
    I am  lucasca-desktop rank 5 (total 16)
    I am  lucasca-desktop rank 11 (total 16)
    I am  lucasca-desktop rank 1 (total 16)
    I am  lucasca-desktop rank 7 (total 16)
    I am  lucasca-desktop rank 0 (total 16)
    I am  lucasca-desktop rank 13 (total 16)
      Slave lucasca-desktop rank 5 executing TASK1 with arg1 0
      Slave lucasca-desktop rank 7 executing TASK1 with arg1 1
      Slave lucasca-desktop rank 8 executing TASK1 with arg1 2
      Slave lucasca-desktop rank 10 executing TASK2 with arg1 4 arg2 8
      Slave lucasca-desktop rank 12 executing TASK2 with arg1 6 arg2 12
      Slave lucasca-desktop rank 14 executing TASK1 with arg1 8
    Master: slave finished is task returning: (True, 2))
    Master: slave finished is task returning: (True, 4, 'something', 'else'))
    Master: slave finished is task returning: (True, 0))
    Master: slave finished is task returning: (True, 1))
    I am  lucasca-desktop rank 3 (total 16)
      Slave lucasca-desktop rank 9 executing TASK3 with arg1 3 arg2 999 arg3 something
    I am  lucasca-desktop rank 4 (total 16)
    I am  lucasca-desktop rank 15 (total 16)
      Slave lucasca-desktop rank 13 executing TASK1 with arg1 7
      Slave lucasca-desktop rank 11 executing TASK1 with arg1 5
      Slave lucasca-desktop rank 1 executing TASK3 with arg1 9 arg2 999 arg3 something
      Slave lucasca-desktop rank 4 executing TASK1 with arg1 11
      Slave lucasca-desktop rank 8 executing TASK2 with arg1 15 arg2 30
      Slave lucasca-desktop rank 3 executing TASK1 with arg1 10
      Slave lucasca-desktop rank 6 executing TASK1 with arg1 13
      Slave lucasca-desktop rank 15 executing TASK2 with arg1 17 arg2 34
    Master: slave finished is task returning: (True, 10))
    Master: slave finished is task returning: (True, 11))
    Master: slave finished is task returning: (True, 13))
    Master: slave finished is task returning: (True, 15, 'something', 'else'))
    Master: slave finished is task returning: (True, 3, 'something'))
    Master: slave finished is task returning: (True, 5))
    Master: slave finished is task returning: (True, 6, 'something', 'else'))
    Master: slave finished is task returning: (True, 7))
    Master: slave finished is task returning: (True, 8))
      Slave lucasca-desktop rank 10 executing TASK3 with arg1 16 arg2 999 arg3 something
      Slave lucasca-desktop rank 7 executing TASK2 with arg1 14 arg2 28
      Slave lucasca-desktop rank 5 executing TASK1 with arg1 12
      Slave lucasca-desktop rank 2 executing TASK3 with arg1 18 arg2 999 arg3 something
      Slave lucasca-desktop rank 8 executing TASK2 with arg1 22 arg2 44
      Slave lucasca-desktop rank 4 executing TASK1 with arg1 20
      Slave lucasca-desktop rank 9 executing TASK1 with arg1 23
      Slave lucasca-desktop rank 13 executing TASK1 with arg1 26

