global class SDO_Tool_qdev_FSLcrew implements Database.Batchable<sObject>{
    String objName;
    Integer daysToAdd;
    String operation;
    Integer order;
    Id territoryId;
    Point originalLocationCoordinate;
    Point newLocationCoordinate;
    
    global SDO_Tool_qdev_FSLcrew(String o, Integer num, String op,Id territory, Point origL, Point newL,Integer i){
        objName=o;
        daysToAdd=num;
        operation=op;
        order = i;
        territoryId = territory;
        originalLocationCoordinate=origL;
        newLocationCoordinate=newL;
    }
    
    global Database.QueryLocator start(Database.BatchableContext BC){
        String query;
        
        
        
        
        if(objName=='ServiceAppointment' && operation=='insert'&&territoryId==null){ //clone services
            query='SELECT ' + GetAllObjectFields('ServiceAppointment') + ',ParentRecordId From ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = true and SDO_Tool_Service_Crew__c = true order by SchedStartTime ';   
        } 
        else if(objName=='ServiceAppointment' && operation=='insert' && territoryId!=null){ //clone services
            query='SELECT ' + GetAllObjectFields('ServiceAppointment') + ',ParentRecordId From ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = true and SDO_Tool_Service_Crew__c = true and ServiceTerritoryId=:territoryId order by SchedStartTime ';   
        }
        system.debug('************ Query:'+query);
        return Database.getQueryLocator(query);
        
    }
    
    global void execute(Database.BatchableContext info, List<sObject> scope){
        system.debug('***************Object: '+ objName+ ' Operation: '+ operation);
        system.debug('*************** Number of records:'+ scope.size());
        List<sObject> clonedObjects = new List<sObject>();
        
        if(objName=='ServiceAppointment' && operation=='insert'){
            system.debug('***************Object: '+ objName+ ' Operation: '+ operation);
            system.debug('*************** Number of records:'+ scope.size());
            
            //Disable Auto Create SAs on all Work Types - will handle this manually
            List<WorkType> lstWorkTypes = [select Id, ShouldAutoCreateSvcAppt from WorkType where ShouldAutoCreateSvcAppt=true];
            for(WorkType wt: lstWorkTypes){
                wt.ShouldAutoCreateSvcAppt = false;
            }
            system.debug('*************** Disabling all WorkTypes:'+ lstWorkTypes);
            update lstWorkTypes;
            
            List<WorkOrder> lstWOs = new List<WorkOrder>();
            List<Id> lstOrigSAIDs = new list<Id>();
            for(Integer i=0; i<scope.size(); i++){
                lstOrigSAIDs.add(scope[i].Id);
            }
            
            //Create Map with Original WO Id and WorkType Id
            List<WorkOrder> lstOrigWOs = [select Id, Priority,WorkTypeId, ServiceTerritoryId,Pricebook2Id, AccountId from WorkOrder where Id in (Select Parentrecordid from Serviceappointment where id in :lstOrigSAIDs) and ServiceTerritoryId != null Limit 1]; /* CA Added accountid for wave data */
            //WorkOrder lstOrigWOs = [select Id, Priority,WorkTypeId, ServiceTerritoryId,Pricebook2Id, AccountId from WorkOrder where Id in (Select Parentrecordid from Serviceappointment where id in :lstOrigSAIDs) and ServiceTerritoryId != null Limit 1];
            system.debug('*************** lstOrigWOs:'+ lstOrigWOs);
            
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
            system.debug('price book' + PriceBk2Id);
            map<id,id> mpOldWoNewWo = new map<id,id>();
            
            for(integer y = 0; y < lstOrigWOs.size(); y++) {
                mpWorkOrderType.put(lstOrigWOs[y].Id,lstOrigWOs[y].WorkTypeId);
                mpWorkOrderPriority.put(lstOrigWOs[y].Id,lstOrigWOs[y].Priority);
                mpAccount.put(lstOrigWOs[y].Id,lstOrigWOs[y].AccountId); 
                mpOldWoNewWo.put(lstOrigWOs[y].Id, lstWOs[y].Id);                
            }
            
            system.debug('finish create key'+mpWorkOrderType+mpWorkOrderPriority+mpAccount+mpOldWoNewWo);
            
            //Clone master ServiceAppointments and then link to a blank WO
            Integer i=0;
            if(order<lstWOs.size()){
                    i=order;
            }else{
                i=lstWOs.size();
            }
            ServiceAppointment s = (ServiceAppointment)scope[order];
            system.debug(i);
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
//cxa         clnService.SchedEndTime = clnService.SchedEndTime != null ? AddDays(clnService.SchedEndTime) : null;
//cxa         clnService.SchedStartTime = clnService.SchedStartTime != null ? AddDays(clnService.SchedStartTime) : null;
            clnService.SDO_Tool_FSLDemoTools_Master_Data__c = false;
            clnService.SDO_Tool_Service_Crew__c=true;
            clnService.External_id__c=null;
            clnService.Status='none'; //cxa added to make sure appointments are unscheduled;
            clnService.SchedStartTime=null; //cxa added to make sure appointments are unscheduled;
            clnService.SchedEndTime=null; //cxa added to make sure appointments are unscheduled;
            if(originalLocationCoordinate!= null && newLocationCoordinate!= null&& clnService.Latitude!=null && clnService.Longitude!=null){
                     Point relocatedCoordinate = GetRelocatedCoordinate(originalLocationCoordinate, newLocationCoordinate, new Point(s.Latitude,s.Longitude));
                    clnService.Latitude = relocatedCoordinate.latitude;
                    clnService.Longitude=relocatedCoordinate.longitude;
            }
            
            try{
                insert clnService;
                system.debug('successfully cloned project '+clonedObjects);
            }catch(DmlException e){
                system.debug('error during clone'+e);
            }
            
            
            update lstWOs;   //Update the WOkrtypes on WOs
            //insert clonedObjects;   //Insert cloned SAs, they're linked to WOs with matching WorkTypes
            
            // insert sa one by one to bypass fsl limitation
            
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
            
            
            
            //if service crew  is true
            //look up to crew team's crew member
            //add assigned resource to service appointment for both service crew team and service crew member
            //
            //ps:service crew member needs to be created/set to cover the appointment slot, service crew member has the id for service crew and service resource
            //assigned resource linked with service crew(servicecrewId, serviceResourceId,serviceappointmentid)
            if(clnService.FSLDemoTools_Service_Resource__c!=null){
                String status;
                if(clnService.Status!='Scheduled'){
                    mpStatuses.put(clnService.Id,clnService.Status);
                }
                
                system.debug('service crew checked');
                ServiceResource sc = [SELECT ServiceCrewId FROM ServiceResource where Id =: clnService.FSLDemoTools_Service_Resource__c];
                AssignedResource ar = new AssignedResource();
                ar.serviceappointmentid = clnService.Id;
                ar.serviceresourceid = clnService.FSLDemoTools_Service_Resource__c;
                /*if(clnService.FSLDemoTools_AR_Actual_Travel_Time__c>120){
                    ar.actualtraveltime = 60;
                }else{
                    ar.actualtraveltime = clnService.FSLDemoTools_AR_Actual_Travel_Time__c; SELECT Latitude,Longitude,TerritoryType FROM ServiceTerritoryMember
                }*/
                if(([SELECT count() FROM ServiceTerritoryMember where TerritoryType = 'P' and ServiceResourceId =:clnService.FSLDemoTools_Service_Resource__c])>0){
                   ar.EstimatedTravelTime = 1;
                    ar.ServiceCrewId = sc.ServiceCrewId;
                    lstARs.add(ar);
     
                }
                            
                //update scm and add crew member resource
                List<ServiceCrewMember> crewList = handleServiceCrew(clnService.FSLDemoTools_Service_Resource__c,clnService.SchedEndTime,daysToAdd);
                system.debug(crewList);
                /*for(ServiceCrewMember crew: crewList){
                    system.debug('service crew member add' + crew);
                    AssignedResource arCrew = new AssignedResource();
                    arCrew.serviceappointmentid = s.Id;
                    arCrew.serviceresourceid = crew.ServiceResourceId;
                    arCrew.actualtraveltime = s.FSLDemoTools_AR_Actual_Travel_Time__c;
                    arCrew.ServiceCrewId = sc.ServiceCrewId;
                    lstARs.add(arCrew);
                    }*/
                
                
                
            }
            
            system.debug('***************Creating ARs lstARs:'+lstARs);
//cxa            insert lstARs;
            
            //Update the statuses of the SAs
//cxa            List<ServiceAppointment> lstSAs = new List<ServiceAppointment>();
//cxa            Set<Id> setSAIds = mpStatuses.keySet();
//cxa            for(Id saId : setSAIds){
//cxa                ServiceAppointment sa = new ServiceAppointment();
//cxa                sa.Id = saId;
//cxa                sa.Status = mpStatuses.get(saId);
//cxa                lstSAs.add(sa);
//cxa            }
//cxa            system.debug('***************Updating statuses on SAs:'+lstSAs);
//cxa            update lstSAs;
        }
       
    }
    
    global void finish(Database.BatchableContext info){
        integer count = [select count() From ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = true and SDO_Tool_Service_Crew__c = true];
        order = order+1;
        system.debug('count records:' + count + 'current index:' + order);

        if(order < count ){ //
            SDO_Tool_qdev_FSLcrew batch = new SDO_Tool_qdev_FSLcrew('ServiceAppointment', daysToAdd, 'insert',territoryId ,originalLocationCoordinate,newLocationCoordinate,order); 
            Database.executeBatch(batch);
        }else{
            AsyncApexJob a = [SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems, CreatedBy.Email FROM AsyncApexJob WHERE Id =: info.getJobId()];
            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            String[] toAddresses = new String[] {a.CreatedBy.Email};
            system.debug('***************email to send to:'+a.CreatedBy.Email);
            mail.setToAddresses(toAddresses);
            mail.setSubject('FSL Demo Tools: Multiday/Crew Appointment move - ' + a.Status);
            mail.setPlainTextBody('Succesfully moved the demo data');
            Messaging.sendEmail(new Messaging.SingleEmailMessage[] { mail });
            system.debug('***************email:'+mail);
        }
        
        
        
    }
    
    private List<ServiceCrewMember> handleServiceCrew(Id idd,DateTime dt,Integer DAYDIFF){
        system.debug('in handling service crew members '+ idd);
        ServiceResource sr = [SELECT ServiceCrewId FROM ServiceResource where id =:idd ];
        list<ServiceCrewMember> crewMembers = [SELECT ServiceResourceId,StartDate,EndDate FROM ServiceCrewMember where ServiceCrewId =:sr.ServiceCrewId];
        for(ServiceCrewMember s : crewMembers){
            if(s.EndDate <= dt){
                 s.EndDate = AddDays(dt);
            }
           
        }
        update crewMembers;
        
        //get all service resource member 
        //check their period 
        //update the time.. 
        //create new assign resource base on service resource
        return crewMembers;
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
    
    private static Point GetRelocatedCoordinate (Point coordinateDistrictOriginal, Point coordinateDistrictNew, Point coordinateObjOriginal) {

    Double bearing = Bearing(coordinateDistrictOriginal, coordinateObjOriginal);
    Double distance = Distance(coordinateDistrictOriginal, coordinateObjOriginal);
    //system.debug('****** bearing: ' + bearing);
    //system.debug('****** distance: ' + distance);
    
    Double bearingRad = bearing * (Math.PI / 180);
    Double distanceAng = distance / 6371;
    
    //Destination coordinates
    Double lat1 = coordinateDistrictNew.LatitudeToRad();
    Double lon1 = coordinateDistrictNew.LongitudeToRad();
    system.debug('****** lat1: ' + lat1);
    system.debug('****** lon1: ' + lon1);
    
    Double lat2 = Math.asin(Math.sin(lat1) * Math.cos(distanceAng) +
                            Math.cos(lat1) * Math.sin(distanceAng) * Math.cos(bearingRad));
    system.debug('****** lat2: ' + lat2);
    
    Double lon2 = lon1 + Math.atan2(Math.sin(bearingRad) * Math.sin(distanceAng) * Math.cos(lat1),
                                    Math.cos(distanceAng) - Math.sin(lat1) * Math.sin(lat2));
    system.debug('****** lon2: ' + lon2);
    
    Point destination = new Point(lat2*(180 / Math.PI), lon2*(180 / Math.PI));
    system.debug('****** destination: ' + destination);
    return destination;
}

private static Double Bearing(Point coordinate1, Point coordinate2) {
    //Returns the inital bearing from coordinate1 to coordinate2
    //system.debug('****** Bearing: ' + coordinate1 + ','+coordinate2);
    Double longitudeDifference = coordinate2.LongitudeToRad() - coordinate1.LongitudeToRad();
    
    Double y = Math.sin(longitudeDifference) * Math.cos(coordinate2.LatitudeToRad());
    Double x = Math.cos(coordinate1.LatitudeToRad()) * Math.sin(coordinate2.LatitudeToRad()) -
        Math.sin(coordinate1.LatitudeToRad()) * Math.cos(coordinate2.LatitudeToRad()) * Math.cos(longitudeDifference);
    
    Double degrees=Modulo((((Math.atan2(y, x) * 180 / Math.PI)) + 360), 360.0);
    return degrees;
}

private static Double Distance(Point coordinate1, Point coordinate2){
    //Returns the distance between the 2 points in meters
    //system.debug('****** Distance: ' + coordinate1 + ','+coordinate2);
    Double d = Math.acos( Math.sin(coordinate1.LatitudeToRad()) * Math.sin(coordinate2.LatitudeToRad())
                         + Math.cos(coordinate1.LatitudeToRad()) * Math.cos(coordinate2.LatitudeToRad()) 
                         * Math.cos((coordinate2.LongitudeToRad()) - (coordinate1.LongitudeToRad()))) * 6371;
    return d;
}

private Static Double Modulo(Decimal a, Decimal b){
    //system.debug('****** Modulo: ' + a + ','+b);
    Integer sign = 1;
    if (a<0){
        sign = -1;
        a = a * -1;
    }
    while(a>=b){
        a-=b;
    }
    return (Double)a * sign;
}
}