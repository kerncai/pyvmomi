#!/usr/bin/env python
#encoding:utf-8 
#kerncai 

import sys,os
import requests
from pyVim import connect
from pyVmomi import vim

'''基于vc-api来获取集群内的相关数据，作为CMDB的数据源入库'''

class action:

    def __init__(self):
        self.v_server = 'ServerIP'
        self.v_user = 'UserName'
        self.v_passwd = 'PassWord'

    def v_server_contect(self):
        #链接vcenter-api，来尝试登陆
        requests.packages.urllib3.disable_warnings()
        try:
            service_instance = connect.SmartConnect(
                                host = self.v_server,
                                user = self.v_user,
                                pwd = self.v_passwd,
                                port = 443)
            return service_instance
        except:
           sys.exit('登陆失败，请检查！goodbye......')

    def v_check_login(self):
        #获取登陆后的session id
        session_id = self.v_server_contect().content.sessionManager.currentSession.key
        print '登陆%s成功，本次登陆的session id 为%s.'%(self.v_server,session_id)
    
    def v_get_object(self):
        #使用rootFolder方式
        vc_rootFolder = self.v_server_contect().RetrieveContent().rootFolder
        datacenters = vc_rootFolder.childEntity
        return datacenters

    def v_get_datacenter(self):
        #获取存储集群
        datacenters = self.v_get_object()
        for dc in datacenters:
            print dc.name


    def v_get_datastore(self):
        #获取单个存储
        datacenters = self.v_get_object()
       # print 'dc_name name capacity freeSpace uncommitted accessible filetype maintenanceMode'
        for dc in datacenters:
            dc_name = dc.name
            datastores = dc.datastoreFolder.childEntity
            for datastore in datastores:
                summary = datastore.summary
                name = summary.name
                capacity = summary.capacity
                freeSpace = summary.freeSpace
                uncommitted = summary.uncommitted
                accessible = summary.accessible
                filetype = summary.type
                maintenanceMode = summary.maintenanceMode
                
               # print dc_name,name,capacity,freeSpace,uncommitted,accessible,filetype,maintenanceMode

    def v_get_cluster(self):
        #获取cluster名字、内存、cpu、状态等相关属性，并将cluster以列表形式return
        cluster_list = []
        datacenters = self.v_get_object()
        #print 'dc_name name totalCpu totalMemory numCpuCores numCpuThreads effectiveCpu effectiveMemory overallStatus'
        for dc in datacenters:
            clusters = dc.hostFolder.childEntity
            for cluster in clusters:
                cluster_list.append(cluster)
                name = cluster.name
                summary = cluster.summary
                totalCpu = summary.totalCpu
                totalMemory = summary.totalMemory
                numCpuCores = summary.numCpuCores
                numCpuThreads = summary.numCpuThreads
                effectiveCpu = summary.effectiveCpu
                effectiveMemory = summary.effectiveMemory
                overallStatus = summary.overallStatus
         #       print dc.name,name,totalCpu,totalMemory,numCpuCores,numCpuThreads,effectiveCpu,effectiveMemory,overallStatus
        return cluster_list

    def v_get_vhost(self):
        #获取cluster列表，通过cluster来获取host
        host_list = []
        clusters = self.v_get_cluster()
        #print 'name;connectionState;powerState;bootTime;os_name;model;uuid;cpudescription;numCpuPackages;numCpuCores;numCpuThreads;hz;overallCpuUsage;memorySize;overallMemoryUsage;biosVersion;key;overallStatus;uptime'
        for cluster in clusters:
            hosts = cluster.host
            for host in hosts:
                host_list.append(host)
                name = host.name
                connectionState = host.runtime.connectionState
                powerState = host.runtime.powerState
                bootTime = host.runtime.bootTime
                os_name = host.summary.config.product.fullName
                model = host.hardware.systemInfo.model
                uuid = host.hardware.systemInfo.uuid
                cpulist = []
                for i in host.hardware.cpuPkg:
                    cpulist.append(i.description)
                cpudescription = cpulist
                numCpuPackages = host.hardware.cpuInfo.numCpuPackages
                numCpuCores = host.hardware.cpuInfo.numCpuCores
                numCpuThreads = host.hardware.cpuInfo.numCpuThreads
                hz = host.hardware.cpuInfo.hz
                overallCpuUsage = host.summary.quickStats.overallCpuUsage
                memorySize = host.hardware.memorySize
                overallMemoryUsage = host.summary.quickStats.overallMemoryUsage
                biosVersion = host.hardware.biosInfo.biosVersion
                key = host.systemResources.key
                overallStatus = host.summary.overallStatus
                uptime = host.summary.quickStats.uptime
    #            print '%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s' %(name,connectionState,powerState,bootTime,os_name,model,uuid,cpudescription,numCpuPackages,numCpuCores,numCpuThreads,hz,overallCpuUsage,memorySize,overallMemoryUsage,biosVersion,key,overallStatus,uptime)
        return host_list
    
    def v_get_vhost_physical_net(self):
        #根据host来获取host的物理网络信息
        host_list = self.v_get_vhost()
        print 'host_name device pci driver wakeOnLanSupported mac autoNegotiateSupported'
        for host in host_list:
            host_name = host.name
            try:
                for pnic in host.config.network.pnic:
                    device = pnic.device
                    pci = pnic.pci
                    driver = pnic.driver
                    wakeOnLanSupported = pnic.wakeOnLanSupported
                    mac = pnic.mac
                    autoNegotiateSupported = pnic.autoNegotiateSupported

                    print host_name,device,pci,driver,wakeOnLanSupported,mac,autoNegotiateSupported
            except AttributeError:
                pass


    def v_get_vhost_vswitch(self):
        #根据host来获取host的vswitch
        host_list = self.v_get_vhost()
        print 'host_name vs_name vs_key numPorts is_bond numPortsAvailable physicalDevice'
        for host in host_list:
            try:
                for vs in host.config.network.vswitch:
                    host_name = host.name
                    vs_name = vs.name
                    vs_key = vs.key
                    numPorts = vs.numPorts
                    is_bond = 0
                    numPortsAvailable = vs.numPortsAvailable
                    numnicDevice = len(vs.spec.bridge.nicDevice)
                    physicalDevice = []
                    if numnicDevice == 2:
                        is_bond = 1
                        physicalDevice.append(vs.spec.bridge.nicDevice[0])
                        physicalDevice.append(vs.spec.bridge.nicDevice[1])
                    else:
                        physicalDevice.append(vs.spec.bridge.nicDevice[0])
                    print host_name,vs_name,vs_key,numPorts,is_bond,numPortsAvailable,physicalDevice
            except AttributeError:
                pass

    def v_get_vhost_portgroup(self):
        #根据host来获取portgroup,以vswitch的key进行关联
        host_list = self.v_get_vhost()
        print 'host_name,vswitchName_name,ps_name,vlanId,ps_key,mac_list'
        for host in host_list:
            try:
                for ps in host.config.network.portgroup:
                    host_name = host.name
                    vswitchName_name = ps.spec.vswitchName
                    ps_name = ps.spec.name
                    vlanId = ps.spec.vlanId
                    ps_key = ps.key
                    mac_list = []
                    for port in ps.port:
                        mac = port.mac[0]
                        mac_list.append(mac)
                    print host_name,vswitchName_name,ps_name,vlanId,ps_key,mac_list

            except AttributeError:
                pass
            
    def v_get_vms(self):
        #根据host来获取vm的相关信息
        host_list = self.v_get_vhost()
        print 'host_name;vm_name;instance_UUID;bios_UUID;guest_os_name;connectionState;path_to_vm;guest_tools_status;memorySizeMB;numCpu;numVirtualDisks;disk_committed;disk_uncommitted;disk_unshared;powerState;overallStatus;last_booted_timestamp;ip_list;macAddress;prot_group'
        for host in host_list:
            for vm in host.vm:
                host_name = host.name
                vm_name = vm.name
                instance_UUID = vm.summary.config.instanceUuid
                bios_UUID = vm.summary.config.uuid
                guest_os_name = vm.summary.config.guestFullName
                connectionState = vm.summary.runtime.connectionState
                path_to_vm = vm.summary.config.vmPathName
                guest_tools_status = vm.guest.toolsStatus
                memorySizeMB =  vm.summary.config.memorySizeMB
                numCpu = vm.summary.config.numCpu
                numVirtualDisks = vm.summary.config.numVirtualDisks
                disk_committed = vm.summary.storage.committed
                disk_uncommitted = vm.summary.storage.uncommitted
                disk_unshared = vm.summary.storage.unshared
                powerState = vm.summary.runtime.powerState
                overallStatus = vm.summary.overallStatus
                last_booted_timestamp = vm.runtime.bootTime
                ip_list = []
                for vnic in vm.guest.net:
                    prot_group = vnic.network
                    ips = vnic.ipAddress
                    for ip in ips:
                        ip_list.append(ip)
                    macAddress = vnic.macAddress    

                print '%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s' %(host_name,vm_name,instance_UUID,bios_UUID,guest_os_name,connectionState,path_to_vm,guest_tools_status,memorySizeMB,numCpu,numVirtualDisks,disk_committed,disk_uncommitted,disk_unshared,powerState,overallStatus,last_booted_timestamp,ip_list,macAddress,prot_group)
                
    def v_server_disconnect(self):
        #退出登陆
        connect.Disconnect(self.v_server_contect())
        print '已从%s退出。' %self.v_server

if __name__ == '__main__':
    run = action()
    run.v_check_login()
    #run.v_get_datacenter()
    #run.v_get_datastore()
    #run.v_get_cluster()
    #run.v_get_vhost()
    #run.v_get_vhost_physical_net()
    #run.v_get_vhost_vswitch()
    #run.v_get_vhost_portgroup()
    run.v_get_vms()
    run.v_server_disconnect()
    del run
