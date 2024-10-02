
# Base class for everything that needs to be updated regularily
class Updateable:
    def update(self):
        pass

    def reset(self):
        pass


###################################################################################


# Base class for handling updateables
class Updater:
    def __init__(self):
        self._updateables = []

    @property
    def updateables(self):
        return self._updateables

    # Add a new Updateable
    def add_updateable(self, u):
        if not isinstance(u, Updateable):
            return
        
        self._updateables.append(u)

    # Update all updateables
    def update(self):
        for u in self._updateables:            
            self.process_pre_update(u)
            u.update()
            #self.process_post_update(u)

    # Called before each updateable has been updated. Can be redefined.
    def process_pre_update(self, updateable):
        pass

    ## Called after each updateable has been updated. Can be redefined.
    #def process_post_update(self, updateable):
    #    pass

    # Reset all updateables
    def reset(self):
        for u in self._updateables:
            u.reset()