//mock for api call out for boost and bury
@isTest 
global with sharing class sdo_scom_boost_and_bury_controller_mock implements HttpCalloutMock {
    public static Integer statusCode = 200;
    public static String requestBody = '{}';
    global HTTPResponse respond(HTTPRequest request) {
        HttpResponse response = new HttpResponse();
        response.setHeader('Content-Type', 'application/json');
        response.setBody(requestBody);
        response.setStatusCode(statusCode);
        return response; 
    }
}