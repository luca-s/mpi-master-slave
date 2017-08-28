# mpi-master-slave: Easy to use mpi master slave code using mpi4py

## Writing you application

Writing a master slave application is as simple as extenging Slave class and implementing the 'do_work' method and creating a Master object that controls the slaves.


```python
from mpi4py import MPI
from mpi.master_slave import Master, Slave
import time

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
```

## Running the application

```
mpiexec -n 4 python example1.py
```

Output:
```
I am  lucasca-desktop rank 0 (total 4)
I am  lucasca-desktop rank 3 (total 4)
I am  lucasca-desktop rank 2 (total 4)
I am  lucasca-desktop rank 1 (total 4)
Slave 3 is going to do task 0
  Slave lucasca-desktop rank 3 executing "Do task" with "0"
Slave 1 is going to do task 1
Slave 3 finished is task and says "I completed my task (0)"
  Slave lucasca-desktop rank 1 executing "Do task" with "1"
Slave 2 is going to do task 2
Slave 3 is going to do task 3
  Slave lucasca-desktop rank 2 executing "Do task" with "2"
  Slave lucasca-desktop rank 3 executing "Do task" with "3"
Slave 2 finished is task and says "I completed my task (2)"
Slave 3 finished is task and says "I completed my task (3)"
Slave 2 is going to do task 4
Slave 3 is going to do task 5
  Slave lucasca-desktop rank 2 executing "Do task" with "4"
Slave 1 finished is task and says "I completed my task (1)"
  Slave lucasca-desktop rank 3 executing "Do task" with "5"
Slave 1 is going to do task 6
  Slave lucasca-desktop rank 1 executing "Do task" with "6"
Slave 2 finished is task and says "I completed my task (4)"
Slave 3 finished is task and says "I completed my task (5)"
Slave 2 is going to do task 7
Slave 3 is going to do task 8
Slave 1 finished is task and says "I completed my task (6)"
  Slave lucasca-desktop rank 3 executing "Do task" with "8"
  Slave lucasca-desktop rank 2 executing "Do task" with "7"
Slave 1 is going to do task 9
Slave 2 finished is task and says "I completed my task (7)"
  Slave lucasca-desktop rank 1 executing "Do task" with "9"
Slave 3 finished is task and says "I completed my task (8)"
Slave 1 finished is task and says "I completed my task (9)"
Task completed (rank 1)
Task completed (rank 0)
Task completed (rank 2)
Task completed (rank 3)

```

## Debugging

We'll open a xterm terminal for each mpi process so that we can debug each process independently:

```
mpiexec -n 4 xterm -e "python example1.py ; bash"
```

*("; bash" is optional - it ensures that the xterm windows will stay open; even if finished)*


Option 1: if you want the debugger to stop at a specific position in the code then add the following at the line where you want the debugger to stop:

```
import ipdb; ipdb.set_trace()
```

Then run the application as above.


Option 2: start the debugger right after each process has started
```
mpiexec -n 4 xterm -e "python -m pdb example1.py ; bash"
```

## Profiling

Eventually you'll probably like to profile your code to understand if there are bottlenecks. To do that you have to first include the profiling module and create one profiler object somewhere in the code


```python
import cProfile

pr = cProfile.Profile()
```

Then you have to start the profiler just before the part of the code you like to profile (you can also start/stop the profiler in different part of the code).
Once you want to see the results (or partial results) stop the profiler and print statistics.

```python
pr.enable()

[...code to be profiled here...]

pr.disable()

pr.print_stats(sort='tottime')
pr.print_stats(sort='cumtime')
```

For example let's say we like to profile the Master process in the example above 

```python
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
```

Output:

```
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

```

From the output above we can see most of the Master time is spent in time.sleep and this is good as the Master doesn't have to be busy as its role is to control the slaves.
