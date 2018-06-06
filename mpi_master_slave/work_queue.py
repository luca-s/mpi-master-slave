__all__=['WorkQueue']

__author__='Luca Scarabello'

class WorkQueue:
    """
    Handle a work queue on a particular Master
    """
   
    def __init__(self, master):
        self.master = master
        self.work_queue           = []
        self.resources_work_queue = {}
        self.slave_resources      = {}

    def done(self):
        """
        Return True when there is no more work to do, the slaves are idle and
        get_completed_work has been called for all the completed slaves
        """
        return self.__work_queues_empty() and self.master.done()

    def add_work(self, data, resource_id=None):
        """
        Add more data to the work queue. When a slave become available this data
        will be passed to it
        """
        self.__add_data(data, resource_id)

    def do_work(self):
        """
        Assign data stored in the work queue to each idle slaves (if any)
        """

        if self.__work_queues_empty():
            return

        #
        # give work to do to each idle slave
        #
        for slave in self.master.get_ready_slaves():
            
            # get next task in the queue
            data, resource_id = self.__get_data_for_slave(slave)
            if data is None:
                break

            # bind this slave to resource_id (that can be None)
            self.slave_resources[slave] = resource_id

            self.master.run(slave, data)

    def get_completed_work(self):
        """
        Fetch the return value of slave that completed its work
        """
        for slave in self.master.get_completed_slaves():
            yield self.master.get_data(slave)


    def __work_queues_empty(self):
        """
        Return True if all the work queues are empty. Some slaves might be still
        processing some data
        """
        return not self.work_queue and not self.resources_work_queue

    def __add_data(self, data, resource_id):
        if resource_id is None:
            # Anonymous work queue
            self.work_queue.append(data)
        else:
            # add a task in the work queue with specifc resource_id
            work_queue = self.resources_work_queue.get(resource_id, list())
            work_queue.append(data)
            self.resources_work_queue[resource_id] = work_queue

    def __pop_data(self, resource_id):
        """
        Pop next task from the work queue with specifc resource_id
        """
        data = None
        if resource_id is None:
            # Anonymous work queue
            if self.work_queue:
                data = self.work_queue.pop(0)
        elif resource_id in self.resources_work_queue:
            # work queue with resource id
            work_queue = self.resources_work_queue[resource_id]
            data = work_queue.pop(0)
            if not work_queue:
                del self.resources_work_queue[resource_id]
        return data

    def __get_data_for_slave(self, slave):
        """
        Try to assign a resource to the same slave that processed it last time,
        This increase caching efficiency as the slave has already acquired the
        resource.
        Also this avoid that different slaves spend time acquiring the same
        resource: this is relevant when the resources are remote (database,
        network directory, etc) or, more generally, when acquiring/loading a
        resource takes time.
        """

        if self.__work_queues_empty():
            return None, None

        resources_to_process = set(self.resources_work_queue.keys())
        not_assigned_resources = resources_to_process - set(self.slave_resources.values())

        resource_id = self.slave_resources.get(slave)
        data = None

        #
        # Try to assign this slave to its previous resource if the slave has
        # a resource already assigned.
        #
        if resource_id is not None:
            data = self.__pop_data(resource_id)        

        #
        # Try to fetch next task from the work queue without resources
        #
        if data is None:
            resource_id = None
            data = self.__pop_data(resource_id)

        #
        # Try to assign this slave to a resource nobody else is using
        #        
        if data is None:
            if not_assigned_resources:
                resource_id = next(iter(not_assigned_resources))
                data = self.__pop_data(resource_id)

        #
        # Finally, assign this slave to a resource in use by other slaves
        #        
        if data is None:
            if resources_to_process:
                resource_id = next(iter(resources_to_process))
                data = self.__pop_data(resource_id)
   
        return data, resource_id

