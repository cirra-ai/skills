public with sharing class SDO_Tool_TrackMixpanel {
    public static boolean postData(Map<string, object> body) {

        try {
            String url = 'https://api.mixpanel.com/track?strict=1';
            String token = '53f404db55440b11dba67f22de17090e';
            String event = 'Demo Rewind';
            String email = UserInfo.getUserEmail();

            List<MixpanelParams> finalParams = new List<MixpanelParams>();

            Map<string, object> properties = new Map<string, object>();
            properties.put('token', token);
            properties.put('distinct_id', email);
            properties.put('time', System.now().getTime());

            properties.putAll(body);

            MixpanelParams params = new MixpanelParams();
            params.event = event;
            params.properties = properties;

            finalParams.add(params);

            system.debug('finalParams... ' + finalParams);

            Http http = new Http();

            HttpRequest req = new HttpRequest();
            req.setEndpoint(url);
            req.setMethod('POST');
            req.setHeader('Content-Type', 'application/json');
            req.setBody(JSON.serialize(finalParams));

            HttpResponse res = http.send(req);
            return true;

        } catch (Exception ex) {
            throw new AuraHandledException(ex.getStackTraceString());
        }
    }

    public class MixpanelParams {
        public string event;
        public Map<string, object> properties;
    }
}