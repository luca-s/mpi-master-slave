from mpi_master_slave import WorkQueue

__all__=['MultiWorkQueue']
__author__ = 'Luca Scarabello'

class MultiWorkQueue:
    """
    Handle multiple work queues
    """
       
    def __init__(self, slaves, masters_details):
        self.slaves = list(slaves)
        self.work_queue = {}
        self.num_slaves = {}
        for task_id, master, num_slaves in masters_details:
            self.work_queue[task_id] = WorkQueue(master)
            self.num_slaves[task_id] = num_slaves

        # assign slaves to Masters
        slaves = list(slaves)
        while slaves:
            for task_id, work_queue in self.work_queue.items():
                if not slaves:
                    break
                num_slaves = self.num_slaves[task_id]
                master     = work_queue.master
                if num_slaves is None or master.num_slaves() < num_slaves:
                    master.add_slave(slaves.pop(0), ready=True)                    
                    

    def done(self):
        for work_queue in self.work_queue.values():
            if not work_queue.done():
                return False
        return True

    def add_work(self, task_id, data, resource_id=None):
        self.work_queue[task_id].add_work(data, resource_id=resource_id)

    def do_work(self):

        for id, work_queue in self.work_queue.items():

            num_slaves = self.num_slaves[id]
            master     = work_queue.master

            if not work_queue.done():
                #
                # if there is still work to do, make sure we have num_slaves in
                # the Master
                #
                if num_slaves is not None and master.num_slaves() < num_slaves:
                    self.__borrow_a_slave(id, master)
    
                work_queue.do_work()

            else:
                #
                # if there is no more work to do, avoid idle slaves lending
                # them to other masters with something in the work queue
                #
                self.__lend_a_slave(id, master)

    def __borrow_a_slave(self, id, master):
        """
        Borrow a slave to Masters that are idle or that don't have
        constraints in the number of slaves
        """
        for other_id, other_work_queue in self.work_queue.items():
            if other_id == id:
                continue   
            other_num_slaves = self.num_slaves[other_id]
            if other_work_queue.done() or other_num_slaves is None:
                other_work_queue.master.move_slave(to_master=master)
                break

    def __lend_a_slave(self, id, master):
        """
        Give a slave to a master with something in the work queue
        """
        for other_id, other_work_queue in self.work_queue.items():
            #
            # avoid masters that have no work to do
            #
            if other_id == id or other_work_queue.done():
                continue
            #
            # give the slave to anybody that doesn't have enought slaves
            # or doesn't have slaves limit
            #
            other_num_slaves = self.num_slaves[other_id]
            if other_num_slaves is None or \
               other_work_queue.master.num_slaves() < other_num_slaves:
                master.move_slave(to_master=other_work_queue.master)
                break

    def get_completed_work(self, task_id):
        return self.work_queue[task_id].get_completed_work()

