from .master_slave import Master

class WorkQueue(object):
    """
    Handle a work queue
    """
   
    def __init__(self, master):
        self.master = master
        self.work_queue = []

    def done(self):
        return not self.work_queue and self.master.done()

    def add_work(self, data):
        self.work_queue.append(data)

    def do_work(self):
        #
        # Keeep starting slaves as long as there is work to do and
        # idle slaves are available
        #
        if self.work_queue:

            #
            # give work to do to each idle slave
            #
            for slave in self.master.get_ready_slaves():
                
                if not self.work_queue:
                    break

                data = self.work_queue.pop(0) # get next task in the queue

                self.master.run(slave, data)


    def get_completed_work(self):
        for slave in self.master.get_completed_slaves():
            yield self.master.get_data(slave)

        
