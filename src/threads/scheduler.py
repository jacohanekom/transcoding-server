__author__ = 'jacohanekom'

import utils, time

class SchedulerThread(utils.Thread):
      modes = ['HandbrakeThread', 'MetadataThread','PublishThread']

      def get_class_identifier(self, class_name):
          counter = 0

          for mode in self.modes:
              if class_name == mode:
                  return counter

              counter += 1

          return -1

      def run(self):
            print 'Starting ' + super(SchedulerThread, self).get_name()

            while True:
                for uuid in super(SchedulerThread, self).registered_files:
                    item = super(SchedulerThread, self).get_storage(uuid)

                    if hasattr(item, "status"):
                        details = item.status.state.split("-")

                        if details[1] == super(SchedulerThread, self).messages[2]:
                            class_indicator = self.get_class_identifier(details[0])

                            if class_indicator == -1 or class_indicator + 2 > len(self.modes):
                                #del super(SchedulerThread, self).registered_files[uuid]
                                item = None
                            else:
                                item.status.state = self.modes[class_indicator+1] + "-" + \
                                                    super(SchedulerThread, self).messages[0]

                    else:
                        status = type('status', (), {})()
                        setattr(status, 'state', self.modes[0] + "-" + super(SchedulerThread, self).messages[0])
                        setattr(status, 'percent', '0')
                        setattr(status, 'time', '0')
                        setattr(status, 'fps', '0')

                        setattr(item, 'status', status)

                    if item:
                        super(SchedulerThread, self).update_storage(uuid,item)

                time.sleep(60)