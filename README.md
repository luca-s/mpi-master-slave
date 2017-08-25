# mpi-master-slave: Easy to use mpi master slave code using mpi4py

## Writing you application

Writing a master slave application is as simple as extenging Slave clase and implementing the 'do_work' method and creating a Master oject that controls the slaves.


```
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
                data = ('Do this', 'are the details')
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
        print('  Slave %s rank %d executing "%s" and "%s"' % (name, rank, task, task_arg) )
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
```

## Running the application

```
mpiexec -n 4 python example1.py
```

Output:
```
I am  lucasca-desktop rank 2 (total 4)
I am  lucasca-desktop rank 1 (total 4)
I am  lucasca-desktop rank 0 (total 4)
Slave 2 ready to do some more work
  Slave lucasca-desktop rank 2 executing "Do this" and "are the details"
I am  lucasca-desktop rank 3 (total 4)
Slave 1 ready to do some more work
Slave 2 finished is task and says I completed my task
  Slave lucasca-desktop rank 1 executing "Do this" and "are the details"
Slave 2 ready to do some more work
Slave 3 ready to do some more work
  Slave lucasca-desktop rank 2 executing "Do this" and "are the details"
  Slave lucasca-desktop rank 3 executing "Do this" and "are the details"
Slave 1 finished is task and says I completed my task
Slave 3 finished is task and says I completed my task
Slave 1 ready to do some more work
Slave 3 ready to do some more work
Slave 2 finished is task and says I completed my task
  Slave lucasca-desktop rank 1 executing "Do this" and "are the details"
  Slave lucasca-desktop rank 3 executing "Do this" and "are the details"
Slave 2 ready to do some more work

```

## Debugging

We open a xterm terminal for each mpi process so that we can debug each process independently on its terminal

```
mpiexec -n 4 xterm -e "python example1.py ; bash"
```

*("; bash" is optional - it ensures that the xterm windows will stay open; even if finished)*


Option 1: if you want the debugger to stop at a particular position in the code then add the following at the line where you want the debugger to stop:

```
import ipdb; ipdb.set_trace()
```

Then run the application as above.


Option 2: start the debugger right after each process has started
```
mpiexec -n 4 xterm -e "python -m pdb example1.py ; bash"
```
