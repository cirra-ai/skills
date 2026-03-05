public class Sdo_Scom_StoreLocatorService implements Sdo_Scom_Int_StoreLocatorService {

    public static List<Sdo_Scom_LocationWrapper> fetchLocations(Integer distance, String unit, Decimal userLatitude, Decimal userLongitude){

        Decimal lat = userLatitude;
        Decimal lng = userLongitude;

        Location loc1 = Location.newInstance(lat,lng);
        Location loc2;

        Decimal dist;
        Decimal roundedDist;

        List<Sdo_Scom_LocationWrapper> storeWrapperList = new List<Sdo_Scom_LocationWrapper>();

        String userId = UserInfo.getUserId();
        User usr = [SELECT Id, AccountId FROM User WHERE Id =: userId];
        String accId = usr.AccountId;

        //List<Schema.Location> storeList = Database.query('SELECT Id, Name, LocationType, VisitorAddressId, Store_Timings__c, Services__c, Facilities__c, (SELECT Id FROM Accounts__r), (SELECT Id, Name, Street, City, State, PostalCode, Country, Phone__c, Latitude, Longitude, Sdo_Scom_Location__c FROM Addresses WHERE DISTANCE(Sdo_Scom_Location__c, GEOLOCATION(' + lat + ', ' + lng + ' ), \'' + String.escapeSingleQuotes(unit) + '\') < ' + String.escapeSingleQuotes(String.valueOf(distance)) + ' ORDER BY DISTANCE(Sdo_Scom_Location__c, GEOLOCATION(' + lat + ', ' + lng + ' ), \'' + String.escapeSingleQuotes(unit) + '\')) FROM Location');
       
        //List<Schema.Location> storeList = Database.query('SELECT Id, Name, Location, LocationType, VisitorAddressId, Store_Timings__c, Services__c, Facilities__c, (SELECT Id FROM Accounts__r WHERE Id =:accId), (SELECT Id, Name, Street, City, State, PostalCode, Country, Phone__c, Latitude, Longitude, Sdo_Scom_Location__c FROM Addresses WHERE DISTANCE(Sdo_Scom_Location__c, GEOLOCATION(' + lat + ', ' + lng + ' ), \'' + String.escapeSingleQuotes(unit) + '\') < ' + String.escapeSingleQuotes(String.valueOf(distance)) + ') FROM Location ORDER BY DISTANCE(Location, GEOLOCATION(' + lat + ', ' + lng + ' ), \'' + String.escapeSingleQuotes(unit) + '\') WHERE LocationType = \'Site\'');

        List<Schema.Location> storeList = Database.query('SELECT Id, Name, Location, LocationType, VisitorAddressId, Sdo_Scom_Store_Timings__c, Sdo_Scom_Services__c, Sdo_Scom_Facilities__c, (SELECT Id FROM Accounts__r), (SELECT Id, Name, Street, City, State, PostalCode, Country, Sdo_Scom_Phone__c, Latitude, Longitude, Sdo_Scom_Location__c FROM Addresses) FROM Location WHERE LocationType = \'Site\'');

        if(!storeList.isEmpty()){
            for(Schema.Location loc : storeList){

                Sdo_Scom_LocationWrapper locWrapper = new Sdo_Scom_LocationWrapper();                

                if(!loc.Addresses.isEmpty()){

                    locWrapper.Addresses = loc.Addresses;
                    //locWrapper.Phone = loc.Addresses[0].Sdo_Scom_Phone__c;
                    locWrapper.VisitorAddressId = loc.VisitorAddressId;
                    locWrapper.LocationType = loc.LocationType;
                    locWrapper.Id = loc.Id;
                    locWrapper.Name = loc.Name;
                    locWrapper.Timings = loc.Sdo_Scom_Store_Timings__c;
                    locWrapper.Services = loc.Sdo_Scom_Services__c;
                    locWrapper.Facilities = loc.Sdo_Scom_Facilities__c;

                    if(loc.Accounts__r.size() == 0){
                        locWrapper.isDefault = false;
                    }
                    else if(loc.Accounts__r.size() > 0){
                        locWrapper.isDefault = true;
                    }
    
                    loc2 = Location.newInstance(locWrapper.Addresses[0].Latitude,locWrapper.Addresses[0].Longitude);
    
                    dist = Location.getDistance(loc1, loc2, unit);
                    roundedDist = dist.setScale(2);
    
                    locWrapper.Distance = roundedDist;
    
                    System.debug('dist->'+locWrapper.Addresses[0].Latitude);
                    storeWrapperList.add(locWrapper);
                }

            }
        }
        System.debug('storeWrapperList ' + storeWrapperList);

        return storeWrapperList;
    }

    public static List<Sdo_Scom_LocationWrapper> fetchPreferredStore(Integer distance, String unit, Decimal userLatitude, Decimal userLongitude){

        Decimal lat = userLatitude;
        Decimal lng = userLongitude;

        Location loc1 = Location.newInstance(lat,lng);
        Location loc2;

        Decimal dist;
        Decimal roundedDist;

        List<Sdo_Scom_LocationWrapper> storeWrapperList = new List<Sdo_Scom_LocationWrapper>();

        List<Schema.Location> storeList = Database.query('SELECT Id, Name, LocationType, VisitorAddressId, Sdo_Scom_Store_Timings__c, Sdo_Scom_Services__c, Sdo_Scom_Facilities__c, (SELECT Id, Name, Street, City, State, PostalCode, Country, Sdo_Scom_Phone__c, Latitude, Longitude, Sdo_Scom_Location__c FROM Addresses WHERE DISTANCE(Sdo_Scom_Location__c, GEOLOCATION(' + lat + ', ' + lng + ' ), \'' + String.escapeSingleQuotes(unit) + '\') < ' + String.escapeSingleQuotes(String.valueOf(distance)) + ' ORDER BY DISTANCE(Sdo_Scom_Location__c, GEOLOCATION(' + lat + ', ' + lng + ' ), \'' + String.escapeSingleQuotes(unit) + '\')) FROM Location WHERE Sdo_Scom_Preferred_Store__c = true AND LocationType = \'Site\'');
        

        if(!storeList.isEmpty()){
            for(Schema.Location loc : storeList){

                Sdo_Scom_LocationWrapper locWrapper = new Sdo_Scom_LocationWrapper();    
                
                System.debug('##'+loc.Addresses);

                locWrapper.Addresses = loc.Addresses;
                //locWrapper.Phone = loc.Addresses[0].Sdo_Scom_Phone__c;
                locWrapper.VisitorAddressId = loc.VisitorAddressId;
                locWrapper.LocationType = loc.LocationType;
                locWrapper.Id = loc.Id;
                locWrapper.Name = loc.Name;
                locWrapper.Timings = loc.Sdo_Scom_Store_Timings__c;
                locWrapper.Services = loc.Sdo_Scom_Services__c;
                locWrapper.Facilities = loc.Sdo_Scom_Facilities__c;

                loc2 = Location.newInstance(locWrapper.Addresses[0].Latitude,locWrapper.Addresses[0].Longitude);

                dist = Location.getDistance(loc1, loc2, unit);
                roundedDist = dist.setScale(2);

                locWrapper.Distance = roundedDist;

                storeWrapperList.add(locWrapper);
            }
        }
        System.debug('storeWrapperList ' + storeWrapperList);

        return storeWrapperList;
    }

    public static void updateDefaultStore(Id storeId){
        
        String userId = UserInfo.getUserId();
        
        User usr = [SELECT Id, AccountId FROM User WHERE Id =: userId];

        String accId = usr.AccountId;

        System.debug('accId ' + accId);
	
        List<Account> accList = new List<Account>([SELECT Id FROM Account WHERE Id =: accId]);
        
        if(!accList.isEmpty()){
            accList[0].Sdo_Scom_Default_Store__c = storeId;
        	update accList[0];
        }
        
    }

    public static void updateLocations(){
        
        String userId = UserInfo.getUserId();
        
        List<Schema.Location> locList = [SELECT Id, Name, Latitude, Longitude, VisitorAddressId, (SELECT Id, Name, Sdo_Scom_Location__Latitude__s, Sdo_Scom_Location__Longitude__s FROM Addresses) FROM Location WHERE VisitorAddressId != ''];

        System.debug('locList-> ' + locList);

        for (Integer i = 0; i < locList.size(); i++) {
            locList[i].Latitude = locList[i].Addresses[0].Sdo_Scom_Location__Latitude__s;
            locList[i].Longitude = locList[i].Addresses[0].Sdo_Scom_Location__Longitude__s;            
        }
        update locList;
    }

}