public with sharing class SDO_Tool_FSLDemoToolsController{
    public SDO_Tool_FSLDemoToolsController() {
    }

  private static Point originalTerritoryCoordinate;
  private static Point newLocationCoordinate;
  
    
  @RemoteAction
  public static Integer getStatus(){
    Integer enqueuedJobs = [SELECT COUNT() FROM AsyncApexJob WHERE JobType='BatchApex' AND Status IN ('Processing','Preparing','Queued')] ;
    return enqueuedJobs;
  }
    
  @RemoteAction
  public static Boolean removeMultidayCrew(){
     Boolean s = true;
    List<ServiceAppointment> sas = [select id From ServiceAppointment Where SDO_Tool_FSLDemoTools_Master_Data__c = false and SDO_Tool_Service_Crew__c = true];
      try{
          delete sas;
      }
      catch(DMLException e){
          system.debug('error in removing service appointments'+ e);
          s = false;
      }
	
     return s;
  }
    
  @RemoteAction
  public static List<ServiceTerritory> GetLocations(){
    List<ServiceTerritory> locations = [SELECT Id,Name, Longitude,Latitude,OperatingHoursId FROM ServiceTerritory];
    return locations;
  }

   @RemoteAction
  public static List<OperatingHours> GetOperatingHours(){
    List<OperatingHours> operatingHours = [SELECT Id,Name, timezone from OperatingHours];
    return operatingHours;
  }
     
  @RemoteAction
  public static List<Schema.PicklistEntry>  GetTimeZones(){
    List<SelectOption> timezoneOptions = new List<SelectOption>();
    Schema.DescribeFieldResult fieldResult = OperatingHours.TimeZone.getDescribe();
    List<Schema.PicklistEntry> ple = fieldResult.getPicklistValues();
    return ple;
  }
     

  @RemoteAction
  public static String GetUserTz(){
    TimeZone tz = UserInfo.getTimeZone();
    return tz.toString();
    //return tz.getDisplayName();
  }

  @RemoteAction
  public static String RestoreData(Integer year, Integer month, Integer day){
        system.debug('*************** Date to restore to (y,m,d):'+ year+','+month+','+day);
    Date dtToRestore = date.newinstance(year, month, day);
    //ResourceAbsence demoEmployeeAbsence = [SELECT Id, Start FROM ResourceAbsence WHERE SDO_Tool_FSLDemoTools_Master_Data__c = TRUE ORDER BY Start ASC LIMIT 1];
    ServiceAppointment sa = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = TRUE and SchedStartTime != null ORDER BY SchedStartTime  ASC LIMIT 1];
    Integer daysDiff = sa.SchedStartTime.dateGMT().daysBetween(dtToRestore);
    system.debug('*************** RestoreData daysDiff:'+daysDiff);
    SDO_Tool_FSLDemoTools_BatchRestoreData batch = new SDO_Tool_FSLDemoTools_BatchRestoreData('ResourceAbsence', daysDiff, 'delete');
    Database.executeBatch(batch);

    RestoreServiceTerritoryMembers();
    RestoreTerritories();

    return 'Success '+ dtToRestore.format();
  }


  @RemoteAction
  public static String MoveDates(Integer year, Integer month, Integer day){
    system.debug('*************** Date to restore to (y,m,d):'+ year+','+month+','+day);
    Date dtToRestore = date.newinstance(year, month, day);
    //ResourceAbsence demoEmployeeAbsence = [SELECT Id, Start FROM ResourceAbsence WHERE SDO_Tool_FSLDemoTools_Master_Data__c = TRUE ORDER BY Start ASC LIMIT 1];
    ServiceAppointment sa = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = false and SDO_Tool_Service_Crew__c = false and FSL__IsMultiDay__c = false and SchedStartTime != null and ParentRecordType IN('WorkOrder','WorkOrderLineItem') ORDER BY SchedStartTime  ASC LIMIT 1];
    Integer daysDiff = sa.SchedStartTime.dateGMT().daysBetween(dtToRestore);
    
    SDO_Tool_FSLDemoTools_BatchMoveDates batch = new SDO_Tool_FSLDemoTools_BatchMoveDates('ServiceTerritoryMember', daysDiff);
    Database.executeBatch(batch);
    return 'Success';
  }
    
  @RemoteAction
  public static String moveMultidayAppointment(Integer year, Integer month, Integer day){
    //List<ServiceAppointment> sas = [SELECT SDO_Tool_FSLDemoTools_Master_Data__c,SDO_Tool_Service_Crew__c FROM ServiceAppointment where SDO_Tool_Service_Crew__c = true and SDO_Tool_FSLDemoTools_Master_Data__c= false ];
	//delete sas;
	
    List<WorkOrder> wo = [select Id from Workorder where id in (select parentrecordid from serviceappointment where SDO_Tool_FSLDemoTools_Master_Data__c = false AND SDO_Tool_Service_Crew__c = true )];
    delete wo;
      
    system.debug('*************** Date to restore to (y,m,d):'+ year+','+month+','+day);
    Date dtToRestore = date.newinstance(year, month, day);
    //ResourceAbsence demoEmployeeAbsence = [SELECT Id, Start FROM ResourceAbsence WHERE SDO_Tool_FSLDemoTools_Master_Data__c = TRUE ORDER BY Start ASC LIMIT 1];
    ServiceAppointment sa = [SELECT Id, SchedStartTime  FROM ServiceAppointment WHERE SDO_Tool_FSLDemoTools_Master_Data__c = TRUE and SDO_Tool_Service_Crew__c = true and SchedStartTime != null ORDER BY SchedStartTime  ASC LIMIT 1];
    Integer daysDiff = sa.SchedStartTime.dateGMT().daysBetween(dtToRestore);
    system.debug('*************** RestoreData daysDiff:'+daysDiff);
      
    SDO_Tool_qdev_FSLcrew batch = new SDO_Tool_qdev_FSLcrew('ServiceAppointment', daysDiff, 'insert',null,null,null,0);
	Database.executeBatch(batch);
    RestoreSingleTerritoriesAndMember('Los Angeles');
          
    return 'Success';
  }


    @RemoteAction
  public static String UpdateTimezones(Id territoryId, String newTZString){
    OperatingHours op = [select id,timezone from operatinghours where id in(select operatinghoursid from ServiceTerritory where id=:territoryId)][0];
    DateTime currentDate = Datetime.now();
    Timezone currentTZ = Timezone.getTimeZone(op.Timezone);
    Timezone newTZ = Timezone.getTimeZone(newTZString);
    Integer numOfMins = (currentTZ.getOffset(currentDate)-newTZ.getOffset(currentDate))/60000;
    system.debug('************ numOfMins:'+numOfMins);
    SDO_Tool_FSLDemoTools_BatchMoveMins batch = new SDO_Tool_FSLDemoTools_BatchMoveMins('ServiceAppointment', territoryId, numOfMins);
    Database.executeBatch(batch);

    UpdateOperatingHoursTZ(op.Id, newTZString);
    UpdateUserTZ(newTZString);
    return 'Success - adding '+ numOfMins +' mins';
  }


  @RemoteAction
  public static String ChangeLocation(Id territoryId, String newLocationName,  Double latitude, Double longitude){
      
        //Getting the original Coordinate
      ServiceTerritory originalTerritory = [SELECT Id,Latitude, Longitude FROM ServiceTerritory WHERE Id=: territoryId LIMIT 1];
      originalTerritoryCoordinate = new Point(originalTerritory.Latitude, originalTerritory.Longitude);
      newLocationCoordinate=new Point(latitude, longitude);
      
      //Updating the Territory Long/Lat
      originalTerritory.Latitude=latitude;
      originalTerritory.Longitude=longitude;
      originalTerritory.Name=newLocationName;
      update originalTerritory;

      SDO_Tool_FSLDemoTools_BatchUpdateLoc batch = new SDO_Tool_FSLDemoTools_BatchUpdateLoc('ServiceTerritoryMember', territoryId, originalTerritoryCoordinate, newLocationCoordinate,0);
      Database.executeBatch(batch);

      return 'Success!';
    }

    private static Void RestoreServiceTerritoryMembers() {
    List<ServiceTerritoryMember> stms = [Select Id, FSLDemoTools_Original_Geolocation__Latitude__s, FSLDemoTools_Original_Geolocation__Longitude__s, Latitude, Longitude From ServiceTerritoryMember where SDO_Tool_FSLDemoTools_Master_Data__c	=true and Territorytype='P'];
      for(ServiceTerritoryMember terr : stms) {
        if(terr.FSLDemoTools_Original_Geolocation__Latitude__s != null && terr.FSLDemoTools_Original_Geolocation__Latitude__s != 0) terr.Latitude = terr.FSLDemoTools_Original_Geolocation__Latitude__s;
        if(terr.FSLDemoTools_Original_Geolocation__Longitude__s != null && terr.FSLDemoTools_Original_Geolocation__Longitude__s != 0) terr.Longitude = terr.FSLDemoTools_Original_Geolocation__Longitude__s;
      } 
      update stms;
    }
    
    private static Void RestoreTerritories() {
      List<ServiceTerritory> territories = [Select Id, Name, FSLDemoTools_Original_Name__c, FSLDemoTools_Original_Geolocation__Latitude__s, FSLDemoTools_Original_Geolocation__Longitude__s, Latitude, Longitude,FSLDemoTools_Original_Timezone__c,OperatingHoursId From ServiceTerritory];
      List<Id> lstOpertingHoursIds = new List<Id>();
      Map<Id,String> mapOperatingHoursTimezones = new  Map<Id,String>();

      for(ServiceTerritory terr : territories) {
        if(terr.FSLDemoTools_Original_Timezone__c!=null && !mapOperatingHoursTimezones.containsKey(terr.OperatingHoursId)){
        mapOperatingHoursTimezones.put(terr.OperatingHoursId, terr.FSLDemoTools_Original_Timezone__c);
        lstOpertingHoursIds.add(terr.OperatingHoursId);
      }

        if(terr.FSLDemoTools_Original_Name__c != null && terr.FSLDemoTools_Original_Name__c != '') terr.Name = terr.FSLDemoTools_Original_Name__c;
        if(terr.FSLDemoTools_Original_Geolocation__Latitude__s != null && terr.FSLDemoTools_Original_Geolocation__Latitude__s != 0) terr.Latitude = terr.FSLDemoTools_Original_Geolocation__Latitude__s;
        if(terr.FSLDemoTools_Original_Geolocation__Longitude__s != null && terr.FSLDemoTools_Original_Geolocation__Longitude__s != 0) terr.Longitude = terr.FSLDemoTools_Original_Geolocation__Longitude__s;
      } 
      update territories;

          system.debug('************ mapOperatingHoursTimezones:'+mapOperatingHoursTimezones);
      List<OperatingHours> operatingHours = [Select Id, timezone from operatinghours where Id in : lstOpertingHoursIds];
       for(OperatingHours op : operatingHours) {
         system.debug('************ mapOperatingHoursTimezones.get(op.Id)!=null:'+mapOperatingHoursTimezones.get(op.Id));
        if(mapOperatingHoursTimezones.get(op.Id)!=null)
            op.Timezone = mapOperatingHoursTimezones.get(op.Id);
       }

       Update operatingHours;

    }
    
    private static Void RestoreSingleTerritoriesAndMember(String t) {
      List<ServiceTerritory> territories = [Select Id, Name, FSLDemoTools_Original_Name__c, FSLDemoTools_Original_Geolocation__Latitude__s, FSLDemoTools_Original_Geolocation__Longitude__s, Latitude, Longitude,FSLDemoTools_Original_Timezone__c,OperatingHoursId From ServiceTerritory where FSLDemoTools_Original_Name__c =: t];
      List<Id> lstOpertingHoursIds = new List<Id>();
      Map<Id,String> mapOperatingHoursTimezones = new  Map<Id,String>();

      for(ServiceTerritory terr : territories) {
        if(terr.FSLDemoTools_Original_Timezone__c!=null && !mapOperatingHoursTimezones.containsKey(terr.OperatingHoursId)){
        mapOperatingHoursTimezones.put(terr.OperatingHoursId, terr.FSLDemoTools_Original_Timezone__c);
        lstOpertingHoursIds.add(terr.OperatingHoursId);
      }

        if(terr.FSLDemoTools_Original_Name__c != null && terr.FSLDemoTools_Original_Name__c != '') terr.Name = terr.FSLDemoTools_Original_Name__c;
        if(terr.FSLDemoTools_Original_Geolocation__Latitude__s != null && terr.FSLDemoTools_Original_Geolocation__Latitude__s != 0) terr.Latitude = terr.FSLDemoTools_Original_Geolocation__Latitude__s;
        if(terr.FSLDemoTools_Original_Geolocation__Longitude__s != null && terr.FSLDemoTools_Original_Geolocation__Longitude__s != 0) terr.Longitude = terr.FSLDemoTools_Original_Geolocation__Longitude__s;
      } 
      update territories;
          system.debug('************ mapOperatingHoursTimezones:'+mapOperatingHoursTimezones);
      List<OperatingHours> operatingHours = [Select Id, timezone from operatinghours where Id in : lstOpertingHoursIds];
       for(OperatingHours op : operatingHours) {
         system.debug('************ mapOperatingHoursTimezones.get(op.Id)!=null:'+mapOperatingHoursTimezones.get(op.Id));
        if(mapOperatingHoursTimezones.get(op.Id)!=null)
            op.Timezone = mapOperatingHoursTimezones.get(op.Id);
       }

       Update operatingHours;
	   RestoreSingleServiceTerritoryMembers(territories[0].id);
    }
    
    private static Void RestoreSingleServiceTerritoryMembers(String idd) {
    List<ServiceTerritoryMember> stms = [Select Id, FSLDemoTools_Original_Geolocation__Latitude__s, FSLDemoTools_Original_Geolocation__Longitude__s, Latitude, Longitude From ServiceTerritoryMember where SDO_Tool_FSLDemoTools_Master_Data__c	=true and Territorytype='P' and ServiceTerritoryId =:idd];
      for(ServiceTerritoryMember terr : stms) {
        if(terr.FSLDemoTools_Original_Geolocation__Latitude__s != null && terr.FSLDemoTools_Original_Geolocation__Latitude__s != 0) terr.Latitude = terr.FSLDemoTools_Original_Geolocation__Latitude__s;
        if(terr.FSLDemoTools_Original_Geolocation__Longitude__s != null && terr.FSLDemoTools_Original_Geolocation__Longitude__s != 0) terr.Longitude = terr.FSLDemoTools_Original_Geolocation__Longitude__s;
      } 
      update stms;
    }

    private static Void UpdateOperatingHoursTZ(Id operatingHoursId, String newTz){
      OperatingHours op = new OperatingHours(Id=operatingHoursId);
      op.TimeZone=newTz;
      Update op;
    } 

    private static Void UpdateUserTZ(String newTz){
      User usr = new User(Id=UserInfo.getUserId());
      usr.TimeZoneSidKey=newTz;
      Update usr;
    } 
    
}