public with sharing class SDO_Service_ConvertToStringCollection {
    
    @invocableMethod(label='SDO Service - Convert any String to String Collection' )
    public static List<Response> execute (List<Request> requests) {

        List<Response> responseList = new List<Response>();

        for (Request curRequest : requests) {
            Response response = new Response();
            String initialString = curRequest.initialString;
            List<String> stringCollection = new List<String>();
            response.stringCollection = curRequest.initialString.split(curRequest.delimiter);
            responseList.add(response);
        }

        return responseList;
    }


    public class Request {
        @invocableVariable(required=true)
        public String initialString;

        @invocableVariable(required=true)
        public String delimiter;

    }

    public class Response {

        @invocableVariable
        public List<String> stringCollection;

    }

    public class InvocableActionException extends Exception {}

}