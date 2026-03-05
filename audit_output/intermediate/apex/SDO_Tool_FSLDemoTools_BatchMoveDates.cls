global class SDO_Tool_FSLDemoTools_BatchMoveDates implements Database.Batchable<sObject> {
	String objName;
	Integer daysToAdd;
    //Integer order;
    //integer count = [select count() from ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = false AND SchedEndTime != null];
        

	global SDO_Tool_FSLDemoTools_BatchMoveDates(String o, Integer num){
		objName=o;
		daysToAdd=num;
        
	}

	global Database.QueryLocator start(Database.BatchableContext BC){
		String query;
		
		//ServiceAppointment
		if(objName=='ServiceAppointment'){
			query='SELECT Id,ArrivalWindowStartTime,ArrivalWindowEndTime,DueDate,EarliestStartTime,SchedEndTime,SchedStartTime from ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = false AND (SDO_Tool_Service_Crew__c = false or FSL__IsMultiDay__c = false) AND SchedEndTime != null ORDER BY SchedStartTime ASC';
		}

		////ServiceTerritoryMember
		else if(objName=='ServiceTerritoryMember'){
			query='SELECT Id,EffectiveEndDate,EffectiveStartDate from ServiceTerritoryMember Where SDO_Tool_FSLDemoTools_Master_Data__c = false and TerritoryType=\'R\'';
		}

		//ResourceAbsence
		else if(objName=='ResourceAbsence'){
			 query='Select Id,End,Start from ResourceAbsence where SDO_Tool_FSLDemoTools_Master_Data__c = false';
			//query='Select ' + GetAllObjectFields('ResourceAbsence') + ',resourceid From ResourceAbsence where SDO_Tool_FSLDemoTools_Master_Data__c = false and RecordType.DeveloperName!=\'Break\'';//RecordType.DeveloperName 
		}
		
		//Capacity
		else if(objName=='ServiceResourceCapacity'){
			query='Select ' + GetAllObjectFields('ServiceResourceCapacity') + ',serviceresourceid From ServiceResourceCapacity Where FSLDemoTools_Master_Data__c = false';
		}

		system.debug('************ Query:'+query);
		return Database.getQueryLocator(query);
	}

	global void execute(Database.BatchableContext info, List<sObject> scope){
		system.debug('*************** Number of records of '+objName+' :'+ scope.size());
		List<sObject> updatedObjects = new List<sObject>();
		List<sObject> newObjects = new List<sObject>();
		
		if(objName=='ServiceAppointment'){
			for(sObject sObj:scope){
				system.debug('************ days to add:'+daysToAdd);
				ServiceAppointment s = (ServiceAppointment)sObj;
				s.ArrivalWindowStartTime = s.ArrivalWindowStartTime != null ? s.ArrivalWindowStartTime.addDays(daysToAdd) : null;
				s.ArrivalWindowEndTime = s.ArrivalWindowEndTime != null ? s.ArrivalWindowEndTime.addDays(daysToAdd) : null;
				s.DueDate = s.DueDate != null ? s.DueDate.addDays(daysToAdd) : null;
				s.EarliestStartTime = s.EarliestStartTime != null ? s.EarliestStartTime.addDays(daysToAdd) : null;
				s.SchedEndTime = s.SchedEndTime != null ? s.SchedEndTime.addDays(daysToAdd) : null;
				s.SchedStartTime = s.SchedStartTime != null ? s.SchedStartTime.addDays(daysToAdd) : null;
				updatedObjects.add(s);
				//update s;
			}
            update updatedObjects;
		}
		else if(objName=='ServiceTerritoryMember'){
			for(sObject sObj:scope){
				ServiceTerritoryMember r = (ServiceTerritoryMember)sObj; 
			    r.EffectiveEndDate = r.EffectiveEndDate != null ? r.EffectiveEndDate.addDays(daysToAdd) : null;
			    r.EffectiveStartDate = r.EffectiveStartDate != null ? r.EffectiveStartDate.addDays(daysToAdd) : null;
               	updatedObjects.add(r);
       		}
               update updatedObjects;
       
		}
		//Need to Clone all existing RAs then delete and then insert the updated cloned ones.
		//else if(objName=='ResourceAbsence'){
		//	for(sObject sObj:scope){
		//		ResourceAbsence a = (ResourceAbsence)sObj;
		//		ResourceAbsence clnEA = a.clone();
		//		clnEA.End = clnEA.End != null ? clnEA.End.addDays(daysToAdd) : null;
		//	    clnEA.Start = clnEA.Start != null ? clnEA.Start.addDays(daysToAdd) : null;
		//		newObjects.add(clnEA);
		//	}
		//}
		//TODO: Need to Clone all existing Capacities then delete and then insert the updated cloned ones.
		else if(objName=='ServiceResourceCapacity'){
			for(sObject sObj:scope){
				ServiceResourceCapacity c = (ServiceResourceCapacity)sObj;
				ServiceResourceCapacity clnC = c.clone();
				clnC.StartDate = clnC.StartDate != null ? clnC.StartDate.addDays(daysToAdd) : null;
				clnC.EndDate = clnC.EndDate != null ? clnC.EndDate.addDays(daysToAdd) : null;
                newObjects.add(clnC);
            }
            update updatedObjects;
		}
				
		if(objName=='ServiceResourceCapacity'){
			delete scope;
			insert newObjects;
		}
		else if (objName=='ResourceAbsence'){
			delete scope;
		}
        
	}

	global void finish(Database.BatchableContext info){
		system.debug('*************** Finish method for '+objName);
		if(objName=='ServiceTerritoryMember'){ //Call the next Batch update
			SDO_Tool_FSLDemoTools_BatchMoveDates batch = new SDO_Tool_FSLDemoTools_BatchMoveDates('ResourceAbsence', daysToAdd);
			Database.executeBatch(batch);
		}
		else if(objName=='ResourceAbsence'){ //Call the next Batch update
			SDO_Tool_FSLDemoTools_BatchMoveDates batch = new SDO_Tool_FSLDemoTools_BatchMoveDates('ServiceAppointment', daysToAdd);
			Database.executeBatch(batch);
		}
		else if(objName=='ServiceAppointment'){ //Call the next Batch update
            SDO_Tool_FSLDemoTools_BatchMoveDates batch = new SDO_Tool_FSLDemoTools_BatchMoveDates('ServiceResourceCapacity', daysToAdd);
            Database.executeBatch(batch);
		}
        /*else if(objName=='ServiceAppointment' && order>=(count-1)){ //Call the next Batch update
            SDO_Tool_FSLDemoTools_BatchMoveDates batch = new SDO_Tool_FSLDemoTools_BatchMoveDates('ServiceResourceCapacity', daysToAdd);
            Database.executeBatch(batch);
		}*/
		else if(objName=='ServiceResourceCapacity'){
            /*if(([SELECT count() FROM ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = false AND SDO_Tool_Service_Crew__c = true AND FSL__IsMultiDay__c = true])>0){

               	List<WorkOrder> wo = [select Id from Workorder where id in (select parentrecordid from serviceappointment where (SDO_Tool_Service_Crew__c = true or FSL__IsMultiDay__c =true) and SDO_Tool_FSLDemoTools_Master_Data__c = false)];
            	delete wo;

                ServiceAppointment saEarliestNonMaster = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = false and SDO_Tool_Service_Crew__c = false and FSL__IsMultiDay__c = false and SchedStartTime != null ORDER BY SchedStartTime  ASC LIMIT 1];
    			ServiceAppointment saEarliestCrewMaster = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = TRUE and SDO_Tool_Service_Crew__c = true and SchedStartTime != null ORDER BY SchedStartTime  ASC LIMIT 1];
                Integer daysDiff = (saEarliestCrewMaster.SchedStartTime.dateGMT().daysBetween(saEarliestNonMaster.SchedStartTime.dateGMT()))+daysToAdd;
                
                SDO_Tool_qdev_FSLcrew batch = new SDO_Tool_qdev_FSLcrew('ServiceAppointment', daysDiff,'insert',null,null,null,0);
                Database.executeBatch(batch);
            }*/
            
            
            //Send Email
            AsyncApexJob a = [SELECT Id, Status, NumberOfErrors, JobItemsProcessed, TotalJobItems, CreatedBy.Email FROM AsyncApexJob WHERE Id =: info.getJobId()];
            Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();
            String[] toAddresses = new String[] {a.CreatedBy.Email};
            mail.setToAddresses(toAddresses);
            mail.setSubject('FSL Demo Tools: Move Dates for Non-crew Demo Data - ' + a.Status);
            mail.setPlainTextBody('Successfully moved all dates on Services, Relocations, Employee Absences and Capacities '+ daysToAdd + ' days.');
            Messaging.sendEmail(new Messaging.SingleEmailMessage[] { mail });
            system.debug('*************** Send email: '+mail);
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
}