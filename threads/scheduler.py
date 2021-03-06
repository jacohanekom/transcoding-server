__author__ = 'jacohanekom'

import utils, time

class SchedulerThread(utils.Base):
      def get_class_identifier(self, class_name):
          counter = 0

          for mode in self.local_modes:
              if class_name == mode:
                  return counter

              counter += 1

          return -1

      def run(self):
            print 'Starting ' + super(SchedulerThread, self).get_name()

            self.local_modes = []
            for mode in super(SchedulerThread, self).get_config()["MODES"]:
                self.local_modes.append(mode.split(".")[1])

            while True:
                for uuid in super(SchedulerThread, self).get_storage():
                    item = super(SchedulerThread, self).get_storage(uuid)

                    if hasattr(item, "status"):
                        details = item.status.state.split("-")

                        if details[1] == super(SchedulerThread, self).messages[2]:
                            class_indicator = self.get_class_identifier(details[0])

                            if class_indicator == -1 or class_indicator + 2 > len(self.local_modes):
                                super(SchedulerThread, self).delete_item(uuid)
                            else:
                                item.status.state = self.local_modes[class_indicator+1] + "-" + \
                                                    super(SchedulerThread, self).messages[0]
                                super(SchedulerThread, self).update_storage(uuid,item)
                        if details[1] == super(SchedulerThread, self).messages[4]:
                            class_indicator = self.get_class_identifier(details[0])

                            item.status.state = self.local_modes[class_indicator-1] + "-" + \
                                                super(SchedulerThread, self).messages[0]
                            super(SchedulerThread, self).update_storage(uuid,item)

                    else:
                        status = type('status', (), {})()
                        setattr(status, 'state', self.local_modes[0] + "-" + super(SchedulerThread, self).messages[0])
                        setattr(status, 'percent', '0')
                        setattr(status, 'time', '0')
                        setattr(status, 'fps', '0')

                        setattr(item, 'status', status)
                        super(SchedulerThread, self).update_storage(uuid,item)

                time.sleep(60)