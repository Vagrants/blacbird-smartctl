"""
blackbird smartctl module

get disk information of S.M.A.R.T using 'smartctl'
"""

import subprocess
from blackbird.plugins import base

__VERSION__ = '0.1.0'


class ConcreteJob(base.JobBase):
    """
    This class is Called by "Executor".
    Get chrony information and send to backend.
    """

    def __init__(self, options, queue=None, logger=None):
        super(ConcreteJob, self).__init__(options, queue, logger)

    def build_items(self):
        """
        main loop
        """

        # ping item
        self.ping()

        # get SMART Attributes
        self.smart_attributes()

    def build_discovery_items(self):
        """
        main loop for lld
        """

        # discovery device name and attribute names
        self.lld_attribute_names()

    def _enqueue(self, key, value):
        """
        set queue item
        """

        item = SmartItem(
            key=key,
            value=value,
            host=self.options['hostname']
        )
        self.queue.put(item, block=False)
        self.logger.debug(
            'Inserted to queue {key}:{value}'
            ''.format(key=key, value=value)
        )

    def _enqueue_lld(self, key, value):
        """
        enqueue lld item
        """

        item = base.DiscoveryItem(
            key=key,
            value=value,
            host=self.options['hostname']
        )
        self.queue.put(item, block=False)
        self.logger.debug(
            'Inserted to lld queue {key}:{value}'
            ''.format(key=key, value=str(value))
        )

    def ping(self):
        """
        send ping item
        """

        self._enqueue('blackbird.smartctl.ping', 1)
        self._enqueue('blackbird.smartctl.version', __VERSION__)

    def smart_attributes(self):
        """
        gather disk information and send data to backend
        """

        for _device in self._scan_disks():
            vals = self._get_disk_attr(_device)

            # not smart supported disk
            if not vals:
                self.logger.debug(
                    '[blackbird smartctl] {0} does not support smart'
                    ''.format(_device)
                )
                continue

            for attr_name in vals.keys():
                # enqueue raw value
                _key = 'smartctl[{0},{1}]'.format(_device, attr_name)
                self._enqueue(_key, vals[attr_name]['raw_value'])

                # enqueue "WHEN_FAILED" status
                _key = 'smartctl.failed[{0},{1}]'.format(_device, attr_name)
                self._enqueue(_key, vals[attr_name]['when_failed'])

    def lld_attribute_names(self):
        """
        discover device attribute name
        """

        for _device in self._scan_disks():
            vals = self._get_disk_attr(_device)

            # not smart supported disk
            if not vals:
                continue

            attr_lld = []
            for attr_name in vals.keys():
                attr_lld.append({
                    '{#SMART_DEVICE}': _device,
                    '{#SMART_ATTR_NAME}': attr_name,
                })

            self._enqueue_lld('smartctl.attribute.LLD', attr_lld)

    def _scan_disks(self):
        """
        execute smartctl --scan and return device list
        """

        _devices = []

        for line in self._smartctl('--scan'):
            _devices.append(line.split()[0])

        return _devices

    def _smartctl(self, *args):
        """
        wrap smartctl execution
        """

        _cmd = ['sudo', self.options['path']]
        for argv in list(args):
            _cmd.append(argv)

        output = ''
        err = ''

        try:
            output, err = subprocess.Popen(
                _cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            ).communicate()
        except OSError:
            raise base.BlackbirdPluginError(
                'can not exec "{cmd}", failed to get disk information'
                ''.format(cmd=' '.join(_cmd))
            )

        if err is not '':
            raise base.BlackbirdPluginError(
                'can not exec "{cmd}" ({err})'
                ''.format(cmd=' '.join(_cmd), err=err.rstrip())
            )

        return output.splitlines()

    def _get_disk_attr(self, device):
        """
        gather disk information by smartctl -A
        """

        ret = dict()
        attrs = self._smartctl('--attributes', device)

        # ignore header 7 lines and last blank line
        for line in attrs[7:-1]:
            cols = line.split()
            attr_name = cols[1]
            ret[attr_name] = dict()
            # raw_value should be integer
            ret[attr_name]['raw_value'] = int(cols[9])
            ret[attr_name]['when_failed'] = cols[8]

        return ret


# pylint: disable=too-few-public-methods
class SmartItem(base.ItemBase):
    """
    Enqued item.
    """

    def __init__(self, key, value, host):
        super(SmartItem, self).__init__(key, value, host)

        self._data = {}
        self._generate()

    @property
    def data(self):
        return self._data

    def _generate(self):
        self._data['key'] = self.key
        self._data['value'] = self.value
        self._data['host'] = self.host
        self._data['clock'] = self.clock


class Validator(base.ValidatorBase):
    """
    Validate configuration.
    """

    def __init__(self):
        self.__spec = None

    @property
    def spec(self):
        self.__spec = (
            "[{0}]".format(__name__),
            "path=string(default='/usr/sbin/smartctl')",
            "hostname=string(default={0})".format(self.detect_hostname()),
        )
        return self.__spec
