global class SDO_Tool_FSLDemoTools_BatchRestoreData implements Database.Batchable<sObject>{
    String objName;
    Integer daysToAdd;
    String operation;
    
    global SDO_Tool_FSLDemoTools_BatchRestoreData(String o, Integer num, String op){
        objName=o;
        daysToAdd=num;
        operation=op;
    }
    
    global Database.QueryLocator start(Database.BatchableContext BC){
        String query;
        
        //ResourceAbsence
        if(objName=='ResourceAbsence' && operation=='delete'){ //delete all non-demo ResourceAbsence
            query='Select Id,End,Start from ResourceAbsence where SDO_Tool_FSLDemoTools_Master_Data__c = false';
        }
        else if(objName=='ResourceAbsence' && operation=='insert'){ //clone ResourceAbsence
            query='Select ' + GetAllObjectFields('ResourceAbsence') + ',resourceid From ResourceAbsence where SDO_Tool_FSLDemoTools_Master_Data__c = true and RecordType.DeveloperName!=\'Break\'';
        }
        
        //FSL__Time_Dependency__c
        else if(objName=='FSL__Time_Dependency__c' && operation=='delete'){ //delete all non-demo FSL__Time_Dependency__c
            query='select id,name from FSL__Time_Dependency__c  where FSL__Service_Appointment_1__c in (select id from serviceappointment where SDO_Tool_FSLDemoTools_Master_Data__c = false)'; 
        }
        //else if(objName=='FSL__Time_Dependency__c' && operation=='insert'){ //clone FSL__Time_Dependency__c
        //    query='SELECT ' + GetAllObjectFields('FSL__Time_Dependency__c') + ',ParentRecordId From ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = true order by SchedStartTime';   
        //}
        
        //Service
        else if(objName=='WorkOrder' && operation=='delete'){ //delete all non-demo WorkOrders and ServiceAppointments
            query='select Id from Workorder where id in (select parentrecordid from serviceappointment where SDO_Tool_FSLDemoTools_Master_Data__c = false)'; 
        }
        else if(objName=='WorkOrderLineItem' && operation=='delete'){ //delete all non-demo WorkOrders and ServiceAppointments
            query='select Id from WorkOrderLineItem where id in (select parentrecordid from serviceappointment where SDO_Tool_FSLDemoTools_Master_Data__c = false)'; 
        }
        else if(objName=='ServiceAppointment' && operation=='insert'){ //clone services
            query='SELECT ' + GetAllObjectFields('ServiceAppointment') + ',ParentRecordId From ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = true and FSL__IsMultiDay__c = false and SDO_Tool_Service_Crew__c = false order by SchedStartTime';   
        }
        
        //ServiceTerritoryMember
        else if(objName=='ServiceTerritoryMember' && operation=='delete'){ //delete non-demo ServiceTerritoryMembers
            query='SELECT Id,EffectiveEndDate,EffectiveStartDate from ServiceTerritoryMember Where SDO_Tool_FSLDemoTools_Master_Data__c = false';
        }
        else if(objName=='ServiceTerritoryMember' && operation=='insert'){ //clone ServiceTerritoryMembers that are of type Relocation
            query='Select ' + GetAllObjectFields('ServiceTerritoryMember') + ',serviceterritoryid From ServiceTerritoryMember Where SDO_Tool_FSLDemoTools_Master_Data__c = true  and TerritoryType=\'R\'';
        }
        
        //ServiceResourceCapacities
        else if(objName=='ServiceResourceCapacity' && operation=='delete'){ //delete non-demo ServiceResourceCapacitys
            query='Select Id,StartDate,EndDate from ServiceResourceCapacity Where FSLDemoTools_Master_Data__c = false';
        }
        
        else if(objName=='ServiceResourceCapacity' && operation=='insert'){ //clone ServiceResourceCapacities
            query='Select ' + GetAllObjectFields('ServiceResourceCapacity') + ',serviceresourceid From ServiceResourceCapacity Where FSLDemoTools_Master_Data__c = true';
        }
        
        system.debug('************ Query:'+query);
        return Database.getQueryLocator(query);
    }
    
    global void execute(Database.BatchableContext info, List<sObject> scope){
        system.debug('***************Object: '+ objName+ ' Operation: '+ operation);
        system.debug('*************** Number of records:'+ scope.size());
        List<sObject> clonedObjects = new List<sObject>();
        
        if(objName=='ServiceAppointment' && operation=='insert'){
            
            //Disable Auto Create SAs on all Work Types - will handle this manually
            List<WorkType> lstWorkTypes = [select Id, ShouldAutoCreateSvcAppt from WorkType where ShouldAutoCreateSvcAppt=true];
            for(WorkType wt: lstWorkTypes){
                wt.ShouldAutoCreateSvcAppt = false;
            }
            system.debug('*************** Disabling all WorkTypes:'+ lstWorkTypes);
            update lstWorkTypes;
            
            
            //Create list of parent blank WOs for the SAs
            List<WorkOrder> lstWOs = new List<WorkOrder>();
            List<Id> lstOrigSAIDs = new list<Id>();
            for(Integer i=0; i<scope.size(); i++){
                lstOrigSAIDs.add(scope[i].Id);
            }
            
            //Create Map with Original WO Id and WorkType Id
            List<WorkOrder> lstOrigWOs = [select Id, Priority,WorkTypeId,ServiceTerritoryId, Pricebook2Id, AccountId from WorkOrder where Id in (Select Parentrecordid from Serviceappointment where id in :lstOrigSAIDs)]; /* CA Added accountid for wave data */
            
            for(WorkOrder originalWorkOrder: lstOrigWOs){
                WorkOrder wo = new WorkOrder();
                wo.Pricebook2Id = originalWorkOrder.Pricebook2Id;
                wo.ServiceTerritoryId = originalWorkOrder.ServiceTerritoryId;
                lstWOs.add(wo);
            }
            insert lstWOs;
            system.debug('*************** New WOs Created:'+ lstWOs);
            
            Map<Id,Id> mpWorkOrderType = new Map<Id,Id>();
            Map<Id,String> mpWorkOrderPriority = new Map<Id,String>(); // DG Added to copy priorities
            Map<Id,Id> mpAccount = new Map<Id,Id>(); /* CA Added for Wave Data */
            ID PriceBk2Id = [select id from pricebook2 where External_ID__c = 'PriceBook.001' limit 1].id;
            map<id,id> mpOldWoNewWo = new map<id,id>();
            
            for(integer y = 0; y < lstOrigWOs.size(); y++) {
                mpWorkOrderType.put(lstOrigWOs[y].Id,lstOrigWOs[y].WorkTypeId);
                mpWorkOrderPriority.put(lstOrigWOs[y].Id,lstOrigWOs[y].Priority);
                mpAccount.put(lstOrigWOs[y].Id,lstOrigWOs[y].AccountId); 
                mpOldWoNewWo.put(lstOrigWOs[y].Id, lstWOs[y].Id);                
            }
            
            //Clone master ServiceAppointments and then link to a blank WO
            Integer i=0;
            DateTime temp;
            for(sObject sObj:scope){
                ServiceAppointment s = (ServiceAppointment)sObj;
                ServiceAppointment clnService = s.clone(false,true);
                if(i<lstWOs.size()){
					clnService.ParentRecordId=lstWOs[i].Id;
                }else{
                    system.debug(lstWOs.size());
                    Integer maxSize = lstWOs.size()-1;
                    clnService.ParentRecordId=lstWOs[maxSize].Id;
                }
                
                clnService.ArrivalWindowStartTime = clnService.ArrivalWindowStartTime != null ? AddDays(clnService.ArrivalWindowStartTime): null;
                clnService.ArrivalWindowEndTime = clnService.ArrivalWindowEndTime != null ? AddDays(clnService.ArrivalWindowEndTime) : null;
                clnService.DueDate = clnService.DueDate != null ? AddDays(clnService.DueDate) : null;
                clnService.EarliestStartTime = clnService.EarliestStartTime != null ? AddDays(clnService.EarliestStartTime) : null;
                clnService.SchedEndTime = clnService.SchedEndTime != null ? AddDays(clnService.SchedEndTime) : null;
                clnService.SchedStartTime = clnService.SchedStartTime != null ? AddDays(clnService.SchedStartTime) : null;
                clnService.SDO_Tool_FSLDemoTools_Master_Data__c = false;
                clnService.External_id__c=null;

                if(clnService.SchedEndTime<clnService.SchedStartTime){
                    temp = clnService.SchedStartTime;
                    clnService.SchedStartTime = clnService.SchedEndTime;
                    clnService.SchedEndTime = temp;
                    system.debug('scheduled start:'+clnService.SchedStartTime+' end:'+clnService.SchedEndTime);
                }

                if(clnService.ArrivalWindowEndTime<clnService.ArrivalWindowStartTime){
                    temp = clnService.ArrivalWindowStartTime;
                    clnService.ArrivalWindowStartTime = clnService.ArrivalWindowEndTime;
                    clnService.ArrivalWindowEndTime = temp;
                    system.debug('arrival start: '+clnService.ArrivalWindowStartTime+' end:'+clnService.ArrivalWindowEndTime);
                }

                clonedObjects.add(clnService);
                
                //Update the Parent WO
                if(i<lstWOs.size()){
                lstWOs[i].WorkTypeId = mpWorkOrderType.get(s.ParentRecordId);
                lstWOs[i].Priority=mpWorkOrderPriority.get(s.ParentRecordId);
                lstWOs[i].AccountId = mpAccount.get(s.ParentRecordId); /* CA added for wave data */
                lstWOs[i].PriceBook2Id = PriceBk2Id;
                }
                i++;
            }
            
            update lstWOs;   //Update the WOkrtypes on WOs
            insert clonedObjects;   //Insert cloned SAs, they're linked to WOs with matching WorkTypes
            
            system.debug('*************** Creating new SAs:'+ clonedObjects);
            //Enabling Auto Create SAs on all Work Types
            for(WorkType wt: lstWorkTypes){
                
                wt.ShouldAutoCreateSvcAppt = true;
            }
            system.debug('*************** Enabling all WorkTypes:'+ lstWorkTypes);
            update lstWorkTypes;
            
            //Create Assigned Resource for new ServiceAppointments
            List<AssignedResource> lstARs = new List<AssignedResource>();
            Map<Id,String> mpStatuses = new Map<Id,String>();
            for(sObject sObj:clonedObjects){
                ServiceAppointment s = (ServiceAppointment)sObj;
                if(s.FSLDemoTools_Service_Resource__c!=null){
                    String status;
                    if(s.Status!='Scheduled'){
                        mpStatuses.put(s.Id,s.Status);
                    }
                    AssignedResource ar = new AssignedResource();
                    ar.serviceappointmentid = s.Id;
                    ar.serviceresourceid = s.FSLDemoTools_Service_Resource__c;
                    //ar.actualtraveltime = s.FSLDemoTools_AR_Actual_Travel_Time__c;
                    ar.EstimatedTravelTime = 1;
                    ar.actualtraveltime = s.FSLDemoTools_AR_Actual_Travel_Time__c;
                    lstARs.add(ar);
                }
            }
            system.debug('***************Creating ARs lstARs:'+lstARs);
            insert lstARs;
            
            //Update the statuses of the SAs
            List<ServiceAppointment> lstSAs = new List<ServiceAppointment>();
            Set<Id> setSAIds = mpStatuses.keySet();
            for(Id saId : setSAIds){
                ServiceAppointment sa = new ServiceAppointment();
                sa.Id = saId;
                sa.Status = mpStatuses.get(saId);
                lstSAs.add(sa);
            }
            system.debug('***************Updating statuses on SAs:'+lstARs);
            update lstSAs;
            
            /* CA Added for wave - clone the products consumed */
            
            list<productconsumed> pcoriglist = new list<productconsumed>([select id, pricebookentryid,quantityconsumed, quantityunitofmeasure, workorderid from productconsumed where workorderid in (select parentrecordid from serviceappointment where id in :lstOrigSAIDs)]);
            list<productconsumed> pclist = new list<productconsumed>();
            for(productconsumed pc : pcoriglist) {
                productconsumed newpc = pc.clone(false,true);
                newpc.workorderid = mpOldWoNewWo.get(pc.workorderid);
                pclist.add(newpc);
            }
            insert pclist; /* commented out for now due to unresolved issue */
            
        }
        else if(objName=='ServiceTerritoryMember' && operation=='insert'){
            for(sObject sObj:scope){
                ServiceTerritoryMember r = (ServiceTerritoryMember)sObj; 
                ServiceTerritoryMember clnSTM = r.clone();
                clnSTM.EffectiveEndDate = r.EffectiveEndDate != null ? AddDays(r.EffectiveEndDate) : null;
                clnSTM.EffectiveStartDate = r.EffectiveStartDate != null ? AddDays(r.EffectiveStartDate) : null;
                clnSTM.SDO_Tool_FSLDemoTools_Master_Data__c = false;    
                clnSTM.External_ID__c=null;
                system.debug('***************Cloned STM:'+clnSTM);           
                clonedObjects.add(clnSTM);
            }
        }
        else if(objName=='ResourceAbsence' && operation=='insert'){
            system.debug('***************Original RAs:'+scope);
            for(sObject sObj:scope){
                ResourceAbsence a = (ResourceAbsence)sObj;
                ResourceAbsence clnEA = a.clone();
                clnEA.End = clnEA.End != null ? AddDays(clnEA.End) : null;
                clnEA.Start = clnEA.Start != null ? AddDays(clnEA.Start) : null;
                clnEA.SDO_Tool_FSLDemoTools_Master_Data__c = false;
                clonedObjects.add(clnEA);
                system.debug('***************Inserted RAs:'+clonedObjects);
            }
        }
        else if(objName=='ServiceResourceCapacity'){
            for(sObject sObj:scope){
                ServiceResourceCapacity c = (ServiceResourceCapacity)sObj;
                ServiceResourceCapacity clnCapacity = c.clone();
                clnCapacity.StartDate = clnCapacity.StartDate != null ? clnCapacity.StartDate.addDays(daysToAdd) : null;
                clnCapacity.EndDate = clnCapacity.EndDate != null ? clnCapacity.EndDate.addDays(daysToAdd) : null;
                clnCapacity.FSLDemoTools_Master_Data__c = false;
                clnCapacity.External_ID__c=null;
                //system.debug('***************Cloned ServiceResourceCapacity:'+clnCapacity);
                clonedObjects.add(clnCapacity);
            }
        }
        
        if(operation == 'delete'){
            system.debug('***************Objects to delete:'+scope);
            delete scope;
        } 
        else if(operation == 'insert' && objName!='ServiceAppointment') insert clonedObjects;
        
    }
    
    global void finish(Database.BatchableContext info){
        if(objName=='ResourceAbsence' && operation=='delete'){ //delete all non-demo FSL__Time_Dependency__c
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('FSL__Time_Dependency__c', daysToAdd, 'delete'); //clone ResourceAbsence
            Database.executeBatch(batch);
        }
        else if(objName=='FSL__Time_Dependency__c' && operation=='delete'){ //delete all non-demo ServiceAppointments
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('WorkOrder', daysToAdd, 'delete'); //clone ResourceAbsence
            Database.executeBatch(batch);
        }
        else if(objName=='WorkOrder' && operation=='delete'){ //delete all non-demo ServiceTerritoryMember
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('WorkOrderLineItem', daysToAdd, 'delete'); //delete non-demo ServiceResourceCapacity
            Database.executeBatch(batch);
        }
        else if(objName=='WorkOrderLineItem' && operation=='delete'){ //delete all non-demo ServiceTerritoryMember
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('ServiceTerritoryMember', daysToAdd, 'delete'); //delete non-demo ServiceResourceCapacity
            Database.executeBatch(batch);
        }
        else if(objName=='ServiceTerritoryMember' && operation=='delete'){ //delete all non-demo ServiceResourceCapacity
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('ServiceResourceCapacity', daysToAdd, 'delete'); //clone demo ServiceAppointment
            Database.executeBatch(batch);
        }
        else if(objName=='ServiceResourceCapacity' && operation=='delete'){ //clone ServiceTerritoryMember
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('ServiceTerritoryMember', daysToAdd, 'insert'); //delete non-demo ServiceTerritoryMember
            Database.executeBatch(batch);
        }
        else if(objName=='ServiceTerritoryMember' && operation=='insert'){ //clone ServiceAppointment
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('ServiceAppointment', daysToAdd, 'insert'); //clone ServiceTerritoryMember
            Database.executeBatch(batch);
        }
        else if(objName=='ServiceAppointment' && operation=='insert'){ //clone ServiceResourceCapacity
            SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('ServiceResourceCapacity', daysToAdd, 'insert'); //delete non-demo ResourceAbsence
            Database.executeBatch(batch);
        }
        
        else if(objName=='ServiceResourceCapacity' && operation=='insert'){ //clone ServiceResourceCapacity
            //Send Email
            AsyncApexJob a = [SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems, CreatedBy.Email FROM AsyncApexJob WHERE Id =: info.getJobId()];
            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            String[] toAddresses = new String[] {a.CreatedBy.Email};
                system.debug('***************email to send to:'+a.CreatedBy.Email);
            mail.setToAddresses(toAddresses);
            mail.setSubject('FSL Demo Tools: Demo Data Reset - ' + a.Status);
            mail.setPlainTextBody('Succesfully restored the demo data');
            Messaging.sendEmail(new Messaging.SingleEmailMessage[] { mail });
            system.debug('***************email:'+mail);
        }
    }
    
    private String GetAllObjectFields(String objectName){
        Schema.SObjectType objSchema = Schema.getGlobalDescribe().get(objectName);
        Map<String, Schema.SObjectField> fieldMap = objSchema.getDescribe().fields.getMap();
        String allObjectFields = 'Id';
        for (String fieldName: fieldMap.keySet()) {
            if (fieldMap.get(fieldName).getDescribe().isUpdateable()) allObjectFields += ', ' + fieldName;
        }
        return allObjectFields;
    }
    
    private DateTime AddDays(DateTime dt) {
        return DateTime.newInstance(dt.addDays(daysToAdd).date(), Time.newInstance(dt.hour(), dt.minute(), dt.second(), 0));
    }
}