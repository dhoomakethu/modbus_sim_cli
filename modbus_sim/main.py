"""
Copyright (c) 2016 Riptide IO, Inc. All Rights Reserved.

Modbus Simu App
===============
"""


try:
    import asyncio
except ImportError:
    import trollius as asyncio

import signal
from modbus_sim.utils.config_parser import YamlConfigParser
from modbus_sim.utils.namespace import Namespace
from modbus_sim.utils.common import path
from modbus_sim.simulation.modbus import ModbusSimu, BLOCK_TYPES
from modbus_sim.utils.logger import set_logger, get_logger


DEFAULT_BLOCK_START = 0
DEFAULT_BLOCK_SIZE = 100


MAP = {
    "coils": "coils",
    'discrete inputs': 'discrete_inputs',
    'input registers': 'input_registers',
    'holding registers': 'holding_registers'
}


@asyncio.coroutine
def simu_factory(simu):
    try:
        simu.run()
    except Exception as e:
        print e
        raise


def handle_sigterm():
    raise SystemExit


class ModbusServer(object):
    """
    Modbus Server class

    """

    # Helpers
    # slaves = ["%s" %i for i in xrange(1, 248)]
    _data_map = {"tcp": {}, "rtu": {}}
    active_slave = None
    server_running = False
    simulating = False
    simu_time_interval = None
    anim = None
    restart_simu = False
    sync_modbus_thread = None
    sync_modbus_time_interval = 5
    _modbus_device = None
    _slaves = {"tcp": None, "rtu": None}

    last_active_port = {"tcp": "", "serial": ""}
    active_server = "tcp"
    _serial_settings_changed = False

    def __init__(self, protocol, settings):
        self.protocol = protocol
        self.settings = settings

    @property
    def modbus_device(self):
        return self._modbus_device

    @modbus_device.setter
    def modbus_device(self, value):
        self._modbus_device = value

    @property
    def slave(self):
        return self._slaves[self.active_server]

    @slave.setter
    def slave(self, value):
        self._slaves[self.active_server] = value

    @property
    def data_map(self):
        return self._data_map[self.active_server]

    @data_map.setter
    def data_map(self, value):
        self._data_map[self.active_server] = value

    def _init_coils(self):
        pass

    def _init_registers(self):
        self.block_start = int(eval(self.config.get("Modbus Protocol",
                                                    "block start")))
        self.block_size = int(eval(self.config.get("Modbus Protocol",
                                                   "block size")))

    def _register_config_change_callback(self, callback, section, key=None):
        self.config.add_callback(callback, section, key)

    def _update_serial_connection(self, *args):
        self._serial_settings_changed = True

    def _create_modbus_device(self):
        self.modbus_device = ModbusSimu(server=self.protocol, **self.settings)

    def start(self):
        # if btn.state == "down":
        self._create_modbus_device()
        self.modbus_device.start()
        self.server_running = True

    def stop(self):
        if self.modbus_device:
            self.modbus_device.stop()
            self.server_running = False

    def add_slaves(self, slaves=[], server={}, modbus_settings={}):
        if not slaves:
            slaves = [1]
        # data = []
        for slave_to_add in slaves:
            self.modbus_device.add_slave(slave_to_add)
            for block_name, block_type in BLOCK_TYPES.items():
                block_start = server.get(block_name, modbus_settings.get(block_name, {})).get("block_start",
                                                                                              DEFAULT_BLOCK_START)
                block_size = server.get(block_name, modbus_settings.get(block_name, {})).get("block_size",
                                                                                             DEFAULT_BLOCK_SIZE)
                default_value = server.get(block_name, modbus_settings.get(block_name, {})).get("default", 0)
                self.modbus_device.add_block(slave_to_add,
                                             block_name, block_type, block_start, block_size)
                self.modbus_device.set_values(slave_to_add, block_name, block_start, [default_value] * block_size)
            # data.append(str(slave_to_add))

    def _process_slave_data(self, data):
        success = True
        data = sorted(data, key=int)
        # last_slave = 1 if not len(data) else data[-1]
        starting_address = int(self.slave_start_add.text)
        end_address = int(self.slave_end_add.text)
        if end_address < starting_address:
            end_address = starting_address
        try:
            slave_count = int(self.slave_count.text)
        except ValueError:
            slave_count = 1

        if str(starting_address) in data:
            self.show_error("slave already present (%s)" % starting_address)
            success = False
            return [success]
        if starting_address < 1:
            self.show_error("slave address (%s)"
                            " should be greater than 0 "% starting_address)
            success = False
            return [success]
        if starting_address > 247:
            self.show_error("slave address (%s)"
                            " beyond supported modbus slave "
                            "device address (247)" % starting_address)
            success = False
            return [success]

        size = (end_address - starting_address) + 1
        size = slave_count if slave_count > size else size

        if (size + starting_address) > 247:
            self.show_error("address range (%s) beyond "
                            "allowed modbus slave "
                            "devices(247)" % (size + starting_address))
            success = False
            return [success]
        self.slave_end_add.text = str(starting_address + size - 1)
        self.slave_count.text = str(size)
        return success, starting_address, size

    def delete_slaves(self, *args):
        selected = self.slave_list.adapter.selection
        slave = self.active_slave
        ct = self.data_models.current_tab
        for item in selected:
            self.modbus_device.remove_slave(int(item.text))
            self.slave_list.adapter.data.remove(item.text)
            self.slave_list._trigger_reset_populate()
            ct.content.clear_widgets(make_dirty=True)
            if self.simulating:
                self.simulating = False
                self.restart_simu = True
                self._simulate()
            self.data_map.pop(slave)

    def update_data_models(self, *args):
        ct = self.data_models.current_tab
        current_tab = MAP[ct.text]

        ct.content.update_view()
        # self.data_map[self.active_slave][current_tab]['dirty'] = False
        _data = self.data_map[self.active_slave][current_tab]
        item_strings = _data['item_strings']
        for i in xrange(int(self.data_count.text)):
            if len(item_strings) < self.block_size:
                updated_data, item_strings = ct.content.add_data(1, item_strings)
                _data['data'].update(updated_data)
                _data['item_strings'] = item_strings
                for k, v in updated_data.iteritems():
                    self.modbus_device.set_values(int(self.active_slave),
                                                  current_tab, k, v)
            else:
                msg = ("OutOfModbusBlockError: address %s"
                       " is out of block size %s" %(len(item_strings),
                                                    self.block_size))
                self.show_error(msg)
                break

    def sync_data_callback(self, blockname, data):
        ct = self.data_models.current_tab
        current_tab = MAP[ct.text]
        if blockname != current_tab:
            current_tab = blockname
        try:
            _data = self.data_map[self.active_slave][current_tab]
            _data['data'].update(data)
            for k, v in data.iteritems():
                self.modbus_device.set_values(int(self.active_slave),
                                              current_tab, k, int(v))
        except KeyError:
            pass

    def delete_data_entry(self, *args):
        ct = self.data_models.current_tab
        current_tab = MAP[ct.text]
        _data = self.data_map[self.active_slave][current_tab]
        item_strings = _data['item_strings']
        deleted, data = ct.content.delete_data(item_strings)
        dm = _data['data']
        for index in deleted:
            dm.pop(index, None)

        if deleted:
            self.update_backend(int(self.active_slave), current_tab, data)
            msg = ("modbus-tk do not support deleting "
               "individual modbus register/discrete_inputs/coils"
               "The data is removed from GUI and the corresponding value is"
               "updated to '0' in backend . ")
            self.show_error(msg)

    def select_slave(self, adapter):
        ct = self.data_models.current_tab
        if len(adapter.selection) != 1:
            # Multiple selection - No Data Update
            ct.content.clear_widgets(make_dirty=True)
            if self.simulating:
                self.simulating = False
                self.restart_simu = True
                self._simulate()
            self.data_model_loc.disabled = True
            self.active_slave = None

        else:
            self.data_model_loc.disabled = False
            if self.restart_simu:
                self.simulating = True
                self.restart_simu = False
                self._simulate()
            self.active_slave = self.slave_list.adapter.selection[0].text
            self.refresh()

    def refresh(self):
        for child in self.data_models.tab_list:
            dm = self.data_map[self.active_slave][MAP[child.text]]['data']
            child.content.refresh(dm)

    def update_backend(self, slave_id, blockname, new_data, ):
        self.modbus_device.remove_block(slave_id, blockname)
        self.modbus_device.add_block(slave_id, blockname,
                                     BLOCK_TYPES[blockname], 0,
                                     self.block_size)
        for k, v in new_data.iteritems():
            self.modbus_device.set_values(slave_id, blockname, k, int(v))

    def change_simulation_settings(self, **kwargs):
        self.data_model_coil.reinit(**kwargs)
        self.data_model_discrete_inputs.reinit(**kwargs)
        self.data_model_input_registers.reinit(**kwargs)
        self.data_model_holding_registers.reinit(**kwargs)

    def change_datamodel_settings(self, key, value):
        if "max" in key:
            data = {"maxval": int(value)}
        else:
            data = {"minval": int(value)}

        if "bin" in key:
            self.data_model_coil.reinit(**data)
            self.data_model_discrete_inputs.reinit(**data)
        else:
            self.data_model_input_registers.reinit(**data)
            self.data_model_holding_registers.reinit(**data)

    def start_stop_simulation(self, btn):
        if btn.state == "down":
            self.simulating = True
        else:
            self.simulating = False
            if self.restart_simu:
                self.restart_simu = False
        self._simulate()

    def _simulate(self):
        self.data_model_coil.start_stop_simulation(self.simulating)
        self.data_model_discrete_inputs.start_stop_simulation(self.simulating)
        self.data_model_input_registers.start_stop_simulation(self.simulating)
        self.data_model_holding_registers.start_stop_simulation(
            self.simulating)

    def _sync_modbus_block_values(self):
        """
        track external changes in modbus block values and sync GUI
        ToDo:
        A better way to update GUI when simulation is on going  !!
        """
        if not self.simulating:
            if self.active_slave:
                _data_map = self.data_map[self.active_slave]
                for block_name, value in _data_map.items():
                    updated = {}
                    for k, v in value['data'].items():
                        actual_data = self.modbus_device.get_values(
                            int(self.active_slave),
                            block_name,
                            int(k),
                            1
                        )
                        if actual_data[0] != int(v):
                            updated[k] = actual_data[0]
                    if updated:
                        value['data'].update(updated)
                        self.refresh()

    def _backup(self):
        if self.slave is not None:
            self.slave.adapter.data = self.slave_list.adapter.data
        self._slave_misc[self.active_server] = [
            self.slave_start_add.text,
            self.slave_end_add.text,
            self.slave_count.text
        ]

    def _restore(self):
        pass
        # if self.slave is None:
        #
        #     adapter = ListAdapter(
        #             data=[],
        #             cls=ListItemButton,
        #             selection_mode='single'
        #     )
        #     self.slave = ListView(adapter=adapter)
        # self.slave_list.adapter.data = self.slave.adapter.data
        # (self.slave_start_add.text,
        #  self.slave_end_add.text,
        #  self.slave_count.text) = self._slave_misc[self.active_server]
        # self.slave_list._trigger_reset_populate()


class ModbusSimuApp(object):

    config = {}
    modbus_settings = {}

    def __init__(self, logger):
        self.servers = []
        self.logger = logger

    def add_server(self, device_config, **kwargs):
        settings = {}
        self.modbus_settings.update(kwargs.get("modbus_settings", {}))
        protocol = device_config.get("protocol", None)
        self.modbus_settings.update(kwargs.get('modbus_settings', {}))
        if protocol == "rtu":
            settings = kwargs.get("serial_settings", {})
            settings["port"] = device_config.get('interface', None)
        elif protocol == "tcp":
            settings = kwargs.get("tcp_settings", {})
        self.logger.info("Adding Modbus %s server: port %s" % (protocol, settings.get("port", "NOT_PROVIDED")))
        self.logger.debug("Device config : %s" % device_config)
        device_config["server"] = ModbusServer(protocol, settings)
        self.servers.append(device_config)

    def run(self):
        self.logger.info("Starting Simulation !")
        for server in self.servers:
            _server = server.get("server")
            _server.start()
            slaves = self._get_slaves(server.get('slaves', ""))
            _server.add_slaves(slaves, server, self.modbus_settings)

    def _get_slaves(self, slaves):
        if isinstance(slaves, int):
            return [slaves]
        else:
            _slaves = []
            try:
                for slave in slaves.split(","):
                    if ".." in slave:
                        start, end = slave.split("..")
                        _range = range(int(start), int(end) + 1)
                        _slaves.extend(_range)

                    else:
                        _slaves.append(int(slave))
            except (TypeError, ValueError):
                print "Invalid range encountered"

            return _slaves

    def stop(self):
        self.logger.info("Stopping simulation")
        for server in self.servers:
            server.get("server").stop()


def setup_loggers(modbus_cfg, simu_log_cfg):
    set_logger("modbus_tk", modbus_cfg.console_log_level.upper(), modbus_cfg.file_logging,
               modbus_cfg.file_log_level.upper(), modbus_cfg.file_log_path)
    set_logger("modbus_simu", simu_log_cfg.console_log_level.upper(), simu_log_cfg.file_logging,
               simu_log_cfg.file_log_level.upper(), simu_log_cfg.file_log_path)


def main(title, args, unknown):
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Parse simulation args
    config_file = args.simu_config
    simu_cfg = Namespace()

    main_logger = get_logger("SIMULATION", "INFO", "%(message)s")
    main_logger.warning("\n\t%s" % title)
    main_logger.warning(">>> Press Ctrl + C to stop Simulation ")
    main_logger.warning("------------------------------------------------"
                        "--------")
    try:
        simu_cfg = Namespace(YamlConfigParser.read(config_file))
    except IOError:
        set_logger("MONITOR", "CRITICAL", True, "CRITICAL",
                   path("~/monitor/log/monitor.log"))
        main_logger.critical("Invalid monitor "
                             "configuration file : %s " % config_file)
        exit(0)

    log_overrides = {"console_log_level": args.console_log_level, "file_logging": args.enable_file_logging,
                     "file_log_path": args.log_file, "file_log_level": args.file_log_level}

    log_overrides = {k: v if v is not None else getattr(simu_cfg.logging.simulation, k)
                     for k, v in log_overrides.items()}
    setup_loggers(simu_cfg.logging.modbus_tk, Namespace(log_overrides))
    simu_logger = get_logger("modbus_simu")
    app = ModbusSimuApp(simu_logger)
    for device in simu_cfg.modbus_devices:
        app.add_server(device, **simu_cfg.to_dict())

    if app.servers:
        try:
            task = [asyncio.Task(simu_factory(app))]
            main_loop = asyncio.get_event_loop()
            main_loop.run_until_complete(asyncio.wait(task))
            # main_loop.run_until_complete(asyncio.wait(simulations['simu_task']))
            main_loop.run_forever()

        except (KeyboardInterrupt, SystemExit):
            app.stop()
    else:
        main_logger.error("No Modbus devices available for simulation , check configuration file ")

    main_logger.info("Bye Bye!!!")

