from mpi4py import MPI
from enum import IntEnum
from mpi_master_slave import exceptions
from abc import ABC, abstractmethod

# Define MPI message tags
Tags = IntEnum('Tags', 'READY START DONE EXIT')

__all__ = ['Master', 'Slave']
__author__ = 'Luca Scarabello'

class Master:
    """
    The main process creates one or more of this class that handle groups of
    slave processes
    """
    
    def __init__(self, slaves = None):
        
        if slaves is None:
            slaves = []
            
        self.comm = MPI.COMM_WORLD
        self.status = MPI.Status()        
        self.slaves = set(slaves)
        self.ready   = set()
        self.running = set()
        self.completed = {}
        
    def num_slaves(self):
        return len(self.slaves)
       
    def add_slave(self, slave, ready):
        self.slaves.add(slave)
        if ready:
            self.ready.add(slave)

    def remove_slave(self, slave):
        if slave in self.get_ready_slaves():
            self.slaves.remove(slave)
            self.ready.remove(slave)
            return True
        return False
        
    def move_slave(self, to_master, slave=None):
        
        if slave is None:
            avail = self.get_ready_slaves()
            if avail:
                slave = next(iter(avail))
            
        if slave is not None and self.remove_slave(slave):
            to_master.add_slave(slave, ready=True)
            return slave
            
        return None

    def get_ready_slaves(self):
                
        # Check processes that are ready to start working again
        possibly_ready = self.slaves - (self.ready | self.running)
        for s in possibly_ready:
                           
            if self.comm.Iprobe(source=s, tag=Tags.READY):
                self.comm.recv(source=s, tag=Tags.READY, status=self.status)
                slave = self.status.Get_source()
                self.ready.add(slave)

        # don't return completed ones, caller needs to collect returned data first
        return self.ready - (self.running | self.completed.keys())


    def run(self, slave, data):
        
        # run the job (is ready) and remove it from ready set
        if slave in self.get_ready_slaves():
            self.comm.send(obj=data, dest=slave, tag=Tags.START)
            self.ready.remove(slave)
            self.running.add(slave)

        # Caller giving a non-ready slave a job is bad! 
        else:
            raise exceptions.SlaveNotReady("Slave {} is busy!")

            
    def get_completed_slaves(self):
        
        # check for completed job and store returned data
        for s in set(self.running):
            
            if self.comm.Iprobe(source=s, tag=Tags.DONE):
                data = self.comm.recv(source=s, tag=Tags.DONE, status=self.status)
                slave = self.status.Get_source()
                self.running.remove(slave)
                self.completed[slave] = data
        
        return set(self.completed.keys())

    def get_data(self, completed_slave):
        
        # onece the caller collect the returned data the job can be run again
        data = None
        if completed_slave in self.get_completed_slaves():
            data = self.completed[completed_slave]
            del self.completed[completed_slave]
        return data            
    
    def done(self):
        return not self.running and not self.completed

    def terminate_slaves(self):
        """
        Call this to make all slaves exit their run loop
        """

        for s in self.slaves:
            self.comm.send(obj=None, dest=s, tag=Tags.EXIT)
        for s in self.slaves:
            self.comm.recv(source=s, tag=Tags.EXIT)
    
    
class Slave(ABC):
    """
    A slave process extend this class, create an instance and invoke the run
    process
    """
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        
    def run(self):
        """
        Invoke this method when ready to put this slave to work
        """
        status = MPI.Status()
        
        while True:
            self.comm.send(None, dest=0, tag=Tags.READY)
            data = self.comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            tag = status.Get_tag()
    
            if tag == Tags.START:
                # Do the work here
                result = self.do_work(data)
                self.comm.send(result, dest=0, tag=Tags.DONE)
            elif tag == Tags.EXIT:
                break
        
        self.comm.send(None, dest=0, tag=Tags.EXIT)
        
    @abstractmethod
    def do_work(self, data):
        """
        Extend this class and override this method to do actual work
        """
        pass
