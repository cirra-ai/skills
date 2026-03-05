global class SDO_Tool_FSLDemoTools_BatchUpdateLoc implements Database.Batchable<sObject>{
    String objName;
    Id territoryId;
    Point originalLocationCoordinate;
    Point newLocationCoordinate;
    Integer order,count;
    
    global SDO_Tool_FSLDemoTools_BatchUpdateLoc(String o, Id terr, Point origL, Point newL, Integer i){
        objName=o;
        territoryId=terr;
        originalLocationCoordinate=origL;
        newLocationCoordinate=newL;
        order = i;
        count = [select count() from ServiceAppointment Where ServiceTerritoryId=:territoryId and SDO_Tool_FSLDemoTools_Master_Data__c = false];
    }
    
    global Database.QueryLocator start(Database.BatchableContext BC){
        String query;
        if(objName=='ServiceTerritoryMember'){ //Move the location on all STM including the master data
            query='SELECT Id,Longitude, Latitude,TerritoryType from ServiceTerritoryMember Where ServiceTerritoryId=:territoryId';
        }
        else if(objName=='ResourceAbsence'){ 
            query='select Id,Longitude,Latitude from ResourceAbsence where SDO_Tool_FSLDemoTools_Master_Data__c=false and ResourceId in (SELECT ServiceResourceId from ServiceTerritoryMember where ServiceTerritoryId=:territoryId) ';
        }
        else if(objName=='ServiceAppointment'){ 
            query='SELECT Id,Longitude,Latitude from ServiceAppointment Where ServiceTerritoryId=:territoryId and SDO_Tool_FSLDemoTools_Master_Data__c = false and FSL__IsMultiDay__c = false and SDO_Tool_Service_Crew__c = false';
        }
        
        system.debug('************ Query:'+query);
        return Database.getQueryLocator(query);
    }
    
    global void execute(Database.BatchableContext info, List<sObject> scope){
        system.debug('*************** Number of records of '+objName+' :'+ scope.size());
        
        if(objName=='ServiceTerritoryMember'){ 
            for(sObject sObj:scope){
                ServiceTerritoryMember stm = (ServiceTerritoryMember)sObj;
                if(stm.Latitude!=null && stm.Longitude!=null){
                    Point relocatedCoordinate = GetRelocatedCoordinate(originalLocationCoordinate, newLocationCoordinate, new Point(stm.Latitude,stm.Longitude));
                    //system.debug('*********Original Lat:'+stm.Latitude);
                    //            system.debug('*********Original Lng:'+stm.Longitude);
                    //system.debug('*********newLat:'+relocatedCoordinate.latitude);
                    //            system.debug('*********newLng:'+relocatedCoordinate.longitude);
                    if(stm.TerritoryType=='P'){
                        //stm.Latitude = newLocationCoordinate.latitude;
                        //stm.Longitude = newLocationCoordinate.longitude;
                        stm.Latitude = relocatedCoordinate.latitude;
                        stm.Longitude = relocatedCoordinate.longitude;
                        system.debug('lat and long new:'+relocatedCoordinate.latitude+''+relocatedCoordinate.longitude);
                    }
                }
            }
            update scope;            
        }
        else if(objName=='ResourceAbsence'){ 
            for(sObject sObj:scope){
                ResourceAbsence r = (ResourceAbsence)sObj;
                if(r.Latitude!=null && r.Longitude!=null){
                    Point relocatedCoordinate = GetRelocatedCoordinate(originalLocationCoordinate, newLocationCoordinate, new Point(r.Latitude,r.Longitude));
                    //system.debug('*********Original Lat:'+r.Latitude);
                    //            system.debug('*********Original Lng:'+r.Longitude);
                    //system.debug('*********newLat:'+relocatedCoordinate.latitude);
                    //            system.debug('*********newLng:'+relocatedCoordinate.longitude);
                    r.Latitude = relocatedCoordinate.latitude;
                    r.Longitude=relocatedCoordinate.longitude;
                }
            }
            update scope;
        }
        else if(objName=='ServiceAppointment'){ 
            for(sObject sObj:scope){
            ServiceAppointment s = (ServiceAppointment)sObj;
            system.debug('in appointments');
            if(s.Latitude!=null && s.Longitude!=null){
                Point relocatedCoordinate = GetRelocatedCoordinate(originalLocationCoordinate, newLocationCoordinate, new Point(s.Latitude,s.Longitude));
                system.debug('*********Original Lat:'+s.Latitude);
                system.debug('*********Original Lng:'+s.Longitude);
                
                s.Latitude = relocatedCoordinate.latitude;
                s.Longitude = relocatedCoordinate.longitude;
                system.debug('*********newLat:'+s.Latitude);
                system.debug('*********newLng:'+s.Longitude);
                //update s;
            }
           }
            update scope;
        }
}  

global void finish(Database.BatchableContext info){
    if (objName == 'ServiceTerritoryMember') {
        SDO_Tool_FSLDemoTools_BatchUpdateLoc batch = new SDO_Tool_FSLDemoTools_BatchUpdateLoc('ResourceAbsence', territoryId, originalLocationCoordinate, newLocationCoordinate,0);
        Database.executeBatch(batch);
    }
    else if (objName == 'ResourceAbsence') {
        SDO_Tool_FSLDemoTools_BatchUpdateLoc batch = new SDO_Tool_FSLDemoTools_BatchUpdateLoc('ServiceAppointment', territoryId, originalLocationCoordinate, newLocationCoordinate,0);
        Database.executeBatch(batch);
    }
    else if(objName=='ServiceAppointment'){ 
        
        if(([SELECT count() FROM ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = false AND ServiceTerritoryId=:territoryId AND SDO_Tool_Service_Crew__c = true AND FSL__IsMultiDay__c = true])>0){
                
                ServiceAppointment saEarliestNonMaster = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = false and SDO_Tool_Service_Crew__c = true and SchedStartTime != null and ServiceTerritoryId=:territoryId ORDER BY SchedStartTime  ASC LIMIT 1];
    			ServiceAppointment saEarliestCrewMaster = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = true and SDO_Tool_Service_Crew__c = true and SchedStartTime != null and ServiceTerritoryId=:territoryId ORDER BY SchedStartTime ASC LIMIT 1];
                Integer daysDiff = (saEarliestCrewMaster.SchedStartTime.dateGMT().daysBetween(saEarliestNonMaster.SchedStartTime.dateGMT()));
                
            	List<FSL__Time_Dependency__c> td = [select id,name from FSL__Time_Dependency__c  where FSL__Service_Appointment_1__c in (select id from serviceappointment where  SDO_Tool_Service_Crew__c = true and SDO_Tool_FSLDemoTools_Master_Data__c = false and SchedStartTime != null)];
                delete td;
                //List<ServiceAppointment> sas = [SELECT SDO_Tool_FSLDemoTools_Master_Data__c,SDO_Tool_Service_Crew__c FROM ServiceAppointment where SDO_Tool_Service_Crew__c = true and SDO_Tool_FSLDemoTools_Master_Data__c= false ];
                //delete sas;
            	//List<ServiceAppointment> sas = [SELECT SDO_Tool_FSLDemoTools_Master_Data__c,SDO_Tool_Service_Crew__c FROM ServiceAppointment where (SDO_Tool_Service_Crew__c = true or FSL__IsMultiDay__c =true) and SDO_Tool_FSLDemoTools_Master_Data__c= false and ServiceTerritoryId=:territoryId ];
                //delete sas;
                List<WorkOrder> wo = [select Id from Workorder where id in (select parentrecordid from serviceappointment where SDO_Tool_FSLDemoTools_Master_Data__c = false AND SDO_Tool_Service_Crew__c = true)];
            	delete wo;
            
                SDO_Tool_qdev_FSLcrew batch = new SDO_Tool_qdev_FSLcrew('ServiceAppointment', daysDiff,'insert',territoryId,originalLocationCoordinate,newLocationCoordinate,0);
                Database.executeBatch(batch);
            }
        
        AsyncApexJob a = [SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems, CreatedBy.Email FROM AsyncApexJob WHERE Id =: info.getJobId()];
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
        String[] toAddresses = new String[] {a.CreatedBy.Email};
            mail.setToAddresses(toAddresses);
        system.debug('****** Status: ' + a.Status);
        system.debug('****** NumberOfErrors: ' + a.NumberOfErrors);
        system.debug('****** TotalJobItems: ' + a.TotalJobItems);
        mail.setSubject('Demo location mover - ' + a.Status);
        mail.setPlainTextBody('Successfully moved the demo data to the new location');
        Messaging.sendEmail(new Messaging.SingleEmailMessage[] { mail });
        
    }
} 


private static Point GetRelocatedCoordinate (Point coordinateDistrictOriginal, Point coordinateDistrictNew, Point coordinateObjOriginal) {
    //need inital district lat long
    //system.debug('*********coordinateDistrictOriginal:'+coordinateDistrictOriginal);
    //system.debug('*********coordinateDistrictNew:'+coordinateDistrictNew);
    //system.debug('*********coordinateObjOriginal:'+coordinateObjOriginal);
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