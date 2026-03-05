/**
 *
     @author        Paul Lucas
     @company       Salesforce
     @description   XDO_Tool_ApiService
     @date          28/12/23

     History:
     When           Who                 What

     TODO:
        - Implement continuation option
            - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_class_System_Continuation.htm#apex_class_System_Continuation
            - https://www.jitendrazaa.com/blog/salesforce/limitless-chaining-of-continuation-object-in-salesforce/
        - Refactor to include other Verbs, eg. PUT, DELETE, PATCH
        - Test class / examples
        - Class security

     Usage:
        - Create a self org SFDCRestAPIClient

        1. Add the dev org to it's own Security Controls -> Remote Sites list
        2. Add an auth header using UserInfo.getSession since it's already an authenticated session
            ( httpRequest.addHeader('Authorization', 'OAuth'+ UserInfo.getSession() )
        3. Make your calls to the REST API
        4. Parse or deserialize the JSON
 */

 public abstract class XDO_Tool_ApiService {
    public static final Integer HTTP_TIMEOUT_MINIMUM = 1; // A value between 1 and 120000 milliseconds.
    public static final Integer HTTP_TIMEOUT_MAXIMUM = 120000; // A value between 1 and 120000 milliseconds.
    public static final String ENCODING_SCHEME = 'UTF-8';
    public static final String HTML_BREAK = '<br/>';
    public static final Integer MAX_MESSAGE_LENGTH = 1024;

    private static final String CALLOUT_PREFIX = 'callout:';
    private static final String CONTENT_TYPE_FORM_URLENCODED = 'application/x-www-form-urlencoded';
    private static final String CONTENT_TYPE_JSON = 'application/json';
    private static final String CONTENT_TYPE_MULTIPART = 'multipart/form-data';
    private static final String AUTHORIZATION_TYPE_INSTANCE = 'XDO_Tool_ApiService.ApiKey{0}Auth';

    public enum CONTENT {
        form, json, multipart
    }

    public static final Map<CONTENT, String> CONTENT_TYPE = new Map<CONTENT, String>{
            CONTENT.form => CONTENT_TYPE_FORM_URLENCODED,
            CONTENT.json => CONTENT_TYPE_JSON,
            CONTENT.multipart => CONTENT_TYPE_MULTIPART
    };

    public static final String AUTHORIZATION_HEADER = 'Authorization';
    public enum AUTHENTICATION_SCHEME_TYPE {
        none, basic, bearer, jwt, digest
    }

    public static final Map<AUTHENTICATION_SCHEME_TYPE, String> AUTHENTICATION_SCHEME = new Map<AUTHENTICATION_SCHEME_TYPE, String>{
            AUTHENTICATION_SCHEME_TYPE.none => '{0}',
            AUTHENTICATION_SCHEME_TYPE.basic => 'Basic {0}',
            AUTHENTICATION_SCHEME_TYPE.bearer => 'Bearer {0}',
            AUTHENTICATION_SCHEME_TYPE.jwt => '{0}',
            AUTHENTICATION_SCHEME_TYPE.digest => '{0}'
    };

    public static final String HEADER_CONTENT_TYPE = 'Content-Type';
    public static final String HEADER_ACCEPT = 'Accept';
    public static final String HEADER_ACCEPT_DELIMITER = ',';
    public static final Map<String, String> DELIMITER = new Map<String, String>{
            'csv' => ',',
            'ssv' => ' ',
            'tsv' => '\t',
            'pipe' => '|'
    };

    public static final Map<String, String> HTTP_ERROR_RESPONSE = new Map<String, String>{
            'code' => '500',
            'status' => 'Error',
            'body' => 'Response is null.'
    };

    public enum HTTP_METHOD {
        GET, POST, PUT, PATCH
    }

    public enum AUTH_TYPE {
        Header, Query
    }

    public abstract class Client {
        protected String scope { get; set; }
        protected Exception calloutException { get; set; }
        protected String calloutMessage { get; set; }

        protected Map<String, Object> headers = new Map<String, Object>();
        protected List<Param> query = new List<Param>();
        protected List<Param> form = new List<Param>();
        protected List<String> accepts = new List<String>();
        protected List<String> contentTypes = new List<String>();
        protected List<String> authenticationMethods = new List<String>();

        @TestVisible
        protected final Map<String, IAuthentication> authentications = new Map<String, IAuthentication>();

        public String endPoint {
            get {
                return !String.isBlank(this.namedCredential) ?
                        CALLOUT_PREFIX + this.namedCredential.trim() :
                        this.endPoint;
            }
            set;
        }

        public String namedCredential {
            get {
                return !String.isBlank(this.namedCredential) ? namedCredential.trim() : '';
            }
            set;
        }

        public Integer timeout {
            get {
                return timeout ?? HTTP_TIMEOUT_MAXIMUM;
            }

            set {
                this.timeout = (value == null ||
                        value < HTTP_TIMEOUT_MINIMUM ||
                        value > HTTP_TIMEOUT_MAXIMUM) ?
                        HTTP_TIMEOUT_MAXIMUM :
                        value;
            }
        }

        /**
         * Constructors
         */
        public Client() {
        }

        public Client(String namedCredential) {
            this.namedCredential = namedCredential;
        }

        /**
         * initialize: Concrete client initialization parameters
         *
         * @param parameters
         *
         * @return
         */
        public virtual Client initialize(Map<String, String> parameters) {
            return this;
        }

        /**
         * setEndPoint: Set the end point
         *
         * @param endPoint
         *
         * @return
         */
        public Client setEndPoint(String endPoint) {
            this.endPoint = endPoint;

            return this;
        }

        /**
         * setNamedCredential: Set the named credential
         *
         * @param namedCredential
         *
         * @return
         */
        public Client setNamedCredential(String namedCredential) {
            this.namedCredential = namedCredential;

            return this;
        }

        /**
         * setTimeout: Set the callout timeout
         *
         * @param timeout
         *
         * @return
         */
        public Client setTimeout(Integer timeout) {
            this.timeout = timeout;

            return this;
        }

        /**
         * getAuthentication: Get an api authentication
         *
         * @param authName
         *
         * @return
         */
        public virtual IAuthentication getAuthentication(String authName) {
            return authentications.get(authName);
        }

        /**
         * setApiKey: Set an api key
         *
         * @param apiKey
         */
        public virtual void setApiKey(String apiKey) {
            for (IAuthentication auth : authentications.values()) {
                if (auth instanceof ApiKeyAuth) {
                    ((ApiKeyAuth) auth).setApiKey(apiKey);
                    return;
                }
            }
            throw new NoSuchElementException('No Api key authentication configured');
        }

        /**
         * setHeader: Set a header
         *
         * @param key
         * @param value
         *
         * @return
         */
        public Client setHeader(String key, Object value) {
            this.headers.put(key, value);

            return this;
        }

        /**
         * setQuery: Set a query parameter
         *
         * @param param
         *
         * @return TODO: https://www.jamessimone.net/blog/joys-of-apex/lazy-iterators/
         */
        public Client setQuery(Param param) {
            removeExistingItem(this.query, param);
            this.query.add(param);

            return this;
        }

        /**
         * setForm: Set a form parameter
         *
         * @param param
         *
         * @return
         */
        public Client setForm(Param param) {
            removeExistingItem(this.form, param);
            this.form.add(param);

            return this;
        }

        /**
         * setAccept: Set an accept type
         *
         * @param mimeType
         *
         * @return
         */
        public Client setAccept(String mimeType) {
            this.accepts = removeExistingItem(this.accepts);
            this.accepts.add(mimeType);

            return this;
        }

        /**
         * setContentType: Set a content type
         *
         * @param mimeType
         *
         * @return
         */
        public Client setContentType(String mimeType) {
            this.contentTypes = removeExistingItem(this.contentTypes);
            this.contentTypes.add(mimeType);

            return this;
        }

        /**
         * setAuthenticationMethod: Set an authentication method
         *
         * @param method
         *
         * @return
         */
        public Client setAuthenticationMethod(String method) {
            this.authenticationMethods.add(method);

            return this;
        }

        /**
         * makeParams: Create a list of Params for a list of values
         *
         * @param name
         * @param values
         *
         * @return
         */
//        public List<Param> makeParams(String name, List<Object> values) {
//            List<Param> pairs = new List<Param>();
//
//            for (Object value : new List<Object>(values)) {
//                pairs.addAll(makeParam(name, value));
//            }
//            return pairs;
//        }
        /**
         * makeParam: Create a Param where the value is a delimited string from a list of values
         *
         * @param name
         * @param values
         * @param format
         *
         * @return
         */
        public List<Param> makeParam(String name, List<Object> values, String format) {
            List<Param> pairs = new List<Param>();

            if (values != null) {
                String delimiter = DELIMITER.get(format);
                pairs.add(new Param(name, String.join(values, delimiter)));
            }
            return pairs;
        }

        /**
         * makeParam: Create a Param
         *
         * @param name
         * @param value
         *
         * @return
         */
        public List<Param> makeParam(String name, Object value) {
            List<Param> pairs = new List<Param>();

            if (!String.isBlank(name) && value != null) {
                pairs.add(new Param(name, String.valueOf(value)));
            }
            return pairs;
        }

        /**
         * resetRequest: Reset request
         *
         * @return
         */
        public Client resetRequest() {
            this.endPoint = '';
            this.headers.clear();
            this.accepts.clear();
            this.contentTypes.clear();
            this.authenticationMethods.clear();
            this.authentications.clear();
            this.form.clear();
            this.query.clear();
            this.calloutException = null;
            this.calloutMessage = null;

            return this;
        }

        /**
         * invoke: Invoke call out
         *
         * @param method
         * @param path
         * @param body
         * @param returnType
         *
         * @return
         */
        public Object invoke(HTTP_METHOD method, String path, Object body, Type returnType) {
            return invoke(method,
                    path,
                    body,
                    null,
                    returnType
            );
        }

        /**
         * invoke: Invoke call out
         *
         * @param method
         * @param path
         * @param body
         * @param pathParams
         * @param returnType
         *
         * @return
         */
        public Object invoke(HTTP_METHOD method, String path, Object body, Map<String, Object> pathParams, Type returnType) {
            ApiServiceResponse response = getResponse(method.name(), path, body, pathParams);
            Object responseBody;

            if (response.isError()) {
                throw new ApiServiceException(response);
            }

            responseBody = deserializeType(returnType, response);
            handleResponse(responseBody);
            resetRequest();

            return responseBody;
        }

        /**
         * getHeaders: Return a map of HttpResponse headers
         *
         * @param response
         *
         * @return
         */
        @TestVisible
        protected virtual Map<String, String> getHeaders(HttpResponse response) {
            Map<String, String> headers = new Map<String, String>();
            List<String> headerKeys = response.getHeaderKeys();

            for (String headerKey : headerKeys) {
                headers.put(headerKey, response.getHeader(headerKey));
            }

            return headers;
        }

        /**
         * toReturnValue: Attempt to parse and return a typed representation of the response
         *
         * @param returnType
         * @param response
         *
         * @return
         */
        @TestVisible
        protected virtual Object deserializeType(Type returnType, ApiServiceResponse response) {
            String body = response.body;
            JSONParser parser;

            if (returnType != null &&
                    response.contentType.toLowerCase().contains(CONTENT_TYPE.get(CONTENT.json)) &&
                    !String.isBlank(body)) {
                try {
                    parser = JSON.createParser(body);
                    parser.nextToken();

                    return parser.readValueAs(returnType);
                } catch (JSONException jsonException) {
                    System.debug(String.format('Error parsing response as JSON: {0}', new List<String>{
                            body
                    }));
                }
            }

            return body;
        }

        /**
         * getResponse: Make a HttpRequest
         *
         * TODO: Normalize for verb and content type..?
         *
         * @param method
         * @param path
         * @param body
         * @param pathParams
         *
         * @return
         */
        @TestVisible
        protected virtual ApiServiceResponse getResponse(String method, String path, Object body, Map<String, Object> pathParams) {
            HttpRequest httpRequest = new HttpRequest();
            ApiServiceResponse httpResponse;
            String contentType;

            applyAuthentication();
            httpRequest.setMethod(method);
            httpRequest.setTimeout(this.timeout);
            httpRequest.setEndpoint(toEndpoint(path, pathParams, this.query));
            contentType = setContentTypeHeader();
            setAcceptHeader();
            setHeaders(httpRequest);

            if (method != HTTP_METHOD.GET.name()) {
                httpRequest.setBody(toBody(contentType, body));
            }

            try {
                System.debug('>>>>> Request Body: ');
                System.debug(httpRequest.getBody());

                // TODO: Standardise event logging (use tracking events?) - before and after
                httpResponse = new ApiServiceResponse(new http()
                        .send(httpRequest));

                System.debug('>>>>> Response: ');
                System.debug(httpResponse);

                if (httpResponse.isError()) {
                    this.handleError(httpResponse);
                }
            } catch (Exception e) {
                // TODO: Force error and review
                this.handleError(httpResponse);
                this.calloutException = e;
                this.calloutMessage = e.getMessage();
                throw new CalloutException(httpResponse.body, e);
            }

            return httpResponse;
        }

        /**
         * getAccessTokenFromCache: Get the access token from the cache.
         *
         * @return
         */
        protected virtual String getAccessTokenFromCache() {
            return null;
        }

        /**
         * getCachedValue: Get a value from the Org cache.
         *
         * @param key
         *
         * @return
         */
        protected virtual Object getCachedOrgValue(String key) {
            Object cachedValue = Cache.Org.get(key);

            return (cachedValue != null) ? cachedValue : null;
        }

        /**
         * cacheOrgValue: Set a value in the Org cache.
         *
         * @param key
         * @param value
         * @param timeToLive
         */
        protected virtual void cacheOrgValue(String key, Object value, Integer timeToLive) {
            Cache.Org.put(key, value, timeToLive);
        }

        /**
         * handleError: Handle error. Implement in subclass, eg. deserialize for each client.
         *
         * @param response
         */
        protected abstract void handleError(ApiServiceResponse response);

        /**
         * handleResponse: Handle response. Implement in subclass, eg. deserialize for each client.
         *
         * @param response
         */
        protected abstract void handleResponse(Object response);

        /**
         * setHeaders: Set HttpRequest headers
         *
         * @param req
         */
        @TestVisible
        protected virtual void setHeaders(HttpRequest req) {
            for (String headerName : this.headers.keySet()) {
                req.setHeader(headerName, String.valueOf(this.headers.get(headerName)));
            }
        }

        /**
         * toBody: Return a transformed request body
         *
         * @param contentType
         * @param body
         *
         * @return TODO: Review form transformation for multi part..
         */
        @TestVisible
        protected virtual String toBody(String contentType, Object body) {
            if (contentType.endsWithIgnoreCase(CONTENT_TYPE.get(CONTENT.form))) {
                return paramsToString(this.form);
            } else if (contentType.equalsIgnoreCase(CONTENT_TYPE.get(CONTENT.json))) {
                return JSON.serialize(body);
            } else {
                return String.valueOf(body);
            }
        }

        /**
         * setContentTypeHeader: Set a single content type header
         *
         * @return TODO: Add boundary for multipart - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type
         */
        @TestVisible
        protected virtual String setContentTypeHeader() {
            String contentType;

            if (this.contentTypes == null || this.contentTypes.isEmpty()) {
                this.headers.put(HEADER_CONTENT_TYPE.toLowerCase(), CONTENT_TYPE.get(CONTENT.json));

                return CONTENT_TYPE.get(CONTENT.json);
            }

            // 'application/json' supersedes all other content types
            for (String ct : this.contentTypes) {
                if (CONTENT_TYPE.get(CONTENT.json) == ct) {
                    this.headers.put(HEADER_CONTENT_TYPE.toLowerCase(), ct);

                    return ct;
                }
            }

            contentType = this.contentTypes.get(0);
            this.headers.put(HEADER_CONTENT_TYPE.toLowerCase(), contentType);

            return contentType;
        }

        /**
         * setAcceptHeader: Set the accept header
         *
         *
         * * TODO: Review logic
         */
        @TestVisible
        protected virtual void setAcceptHeader() {
            if (this.accepts == null || this.accepts.isEmpty()) {
                this.headers.put(HEADER_ACCEPT, CONTENT_TYPE.get(CONTENT.json));

                return;
            }

            // 'application/json' supersedes all other accept headers
            for (String accept : this.accepts) {
                if (CONTENT_TYPE.get(CONTENT.json) == accept) {
                    this.headers.put(HEADER_ACCEPT, CONTENT_TYPE.get(CONTENT.json));

                    return;
                }
            }

            if (!this.accepts.isEmpty()) {
                this.headers.put(HEADER_ACCEPT, String.join(this.accepts, HEADER_ACCEPT_DELIMITER));
            }
        }

        /**
         * setAuthentication: Set authentication method
         *
         * @param authType
         * @param scheme
         * @param key
         *
         * @return
         */
        protected virtual Client setAuthentication(AUTH_TYPE authType, String scheme, String key) {
            ApiKeyAuth authentication = (ApiKeyAuth) Type.forName(String.format(AUTHORIZATION_TYPE_INSTANCE, new List<String>{
                    authType.name()
            })).newInstance();

            authentication.setApiKey(String.format(scheme, new List<String>{
                    key
            }));

            authentications.clear();
            authentications.put(XDO_Tool_ApiService.AUTHORIZATION_HEADER, authentication);

            return this;
        }

        /**
         * applyAuthentication: Apply associated authentication key(s)
         */
        @TestVisible
        protected virtual void applyAuthentication() {
            for (IAuthentication auth : getAuthMethods()) {
                auth.apply(this.headers, this.query);
            }
        }

        /**
         * getAuthMethods: Return a list of registered authentication methods
         *
         * @return
         */
        @TestVisible
        protected virtual List<IAuthentication> getAuthMethods() {
            List<IAuthentication> methods = new List<IAuthentication>();

            if (this.authenticationMethods == null || this.authenticationMethods.isEmpty()) {
                methods.addAll(authentications.values());
            } else {
                for (String name : this.authenticationMethods) {
                    methods.add(authentications.get(name));
                }
            }

            return methods;
        }

        /**
         * toPath: Merge the path route fields
         *
         * @param path
         * @param params
         *
         * @return
         */
        @TestVisible
        protected virtual String toPath(String path, Map<String, Object> params) {
            String formatted = path;

            if (params != null) {
                for (String key : params.keySet()) {
                    formatted = formatted.replace('{' + key + '}', String.valueOf(params.get(key)));
                }
            }

            return formatted;
        }

        /**
         * toEndpoint: Return a formed endpoint
         *
         * @param path
         * @param params
         * @param queryParams
         *
         * @return
         */
        @TestVisible
        protected virtual String toEndpoint(String path, Map<String, Object> params, List<Param> queryParams) {
            String query = '?' + paramsToString(queryParams);
            String fullPath = toPath(path, params);
            String pathName = fullPath.substringBefore('#');
            String hash = fullPath.substring(pathName?.length());

            return String.format('{0}{1}{2}{3}', new List<String>{
                    this.endPoint, pathName, query.removeEnd('?'), hash
            }).replace('??', '?');
        }

        /**
         * paramsToString: Convert params to querystring
         *
         * @param params
         *
         * @return
         */
        @TestVisible
        protected virtual String paramsToString(List<Param> params) {
            List<String> queryString = new List<String>();

            for (Param p : params) {
//                queryStringList.add(EncodingUtil.urlEncode(p.toString(), ENCODING_SCHEME)); // Double escapes single quotes
                queryString.add(p.toString());
            }

            return String.join(queryString, '&');
        }

        /**
         * @param source : Source list
         * @param item : item to remove
         */
        private void removeExistingItem(List<Param> source, Param item) {
            Integer length = source != null ? source.size() - 1 : -1;

            for (Integer i = length; i >= 0; i--) {
                if (item.getName() == source[i].getName()) {
                    source.remove(i);
                }
            }
        }

        /**
         * @param source : Source list
         *
         * @return
         */
        private List<String> removeExistingItem(List<String> source) {
            return new List<String>(new Set<String>(source));
        }
    }

//    public class OrgCacheController {
//
////        put(key, value, ttlSecs)
//
//        public class xxxAccessTokenCache implements Cache.CacheBuilder {
//
//            /**
//             * doLoad: Get the access token from the user record
//             *
//             * Cache.SessionPartition sessionPartition = Cache.Session.getPartition('local.Default');
//             *
//             * @param userId
//             *
//             * @return
//             */
//            public Object doLoad(String userId) {
//
//                String xxxAccessToken = '';
//
////            // Get the user
////            List<User> user = [
////                    SELECT Id,
////                            xxx_Access_Token__c
////                    FROM User
////                    WHERE Id = :userId
////                    LIMIT 1
////            ];
////
////            // Test for a user
////            if (null != user && user.size() > 0) {
////                xxxAccessToken = user[0].xxx_Access_Token__c;
////            }
//
//                return xxxAccessToken;
//            }
//        }

    public interface IAuthentication {
        void apply(Map<String, Object> headers, List<Param> query);
    }

    public abstract class ApiKeyAuth implements IAuthentication {
        protected String paramName;
        protected String key = '';

        public ApiKeyAuth() {
            this.paramName = XDO_Tool_ApiService.AUTHORIZATION_HEADER;
        }

        public void setParamName(String paramName) {
            this.paramName = paramName;
        }

        public void setApiKey(String key) {
            this.key = key;
        }

        private String getApiKey() {
            return key;
        }
    }

    public class ApiKeyQueryAuth extends ApiKeyAuth {
        public ApiKeyQueryAuth() {
            super();
        }

        public ApiKeyQueryAuth(String paramName) {
            this.paramName = paramName;
        }

        public void apply(Map<String, Object> headers, List<Param> query) {
            query.add(new Param(paramName, key));
        }
    }

    public class ApiKeyHeaderAuth extends ApiKeyAuth {
        public ApiKeyHeaderAuth() {
            super();
        }

        public ApiKeyHeaderAuth(String paramName) {
            this.paramName = paramName;
        }

        public void apply(Map<String, Object> headers, List<Param> query) {
            headers.put(this.paramName, key);
        }
    }

    public class Param {
        private String name, value;

        public Param(String name, String value) {
            this.name = name;
            this.value = value;
        }

        public String getName() {
            return this.name;
        }

        public override String toString() {
            return EncodingUtil.urlEncode(name, 'UTF-8') + '=' + EncodingUtil.urlEncode(value, 'UTF-8');
        }
    }

    public virtual class ApiServiceResponse {
        private Boolean ignoreError = false;
        public String contentType {
            get {
                if (this.contentType == null) {
                    this.contentType = '';
                }
                return this.contentType;
            }
            private set {
                this.contentType = value;
            }
        }

        public Integer statusCode {
            get {
                if (this.statusCode == null) {
                    this.statusCode = 200;
                }
                return this.statusCode;
            }
            private set {
                this.statusCode = value;
            }
        }

        public String status {
            get {
                if (this.status == null) {
                    this.status = 'OK';
                }
                return this.status;
            }
            private set {
                this.status = value;
            }
        }

        public String body {
            get {
                if (this.body == null) {
                    this.body = '';
                }
                return this.body;
            }
            private set {
                this.body = value;
            }
        }

        public ApiServiceResponse() {
        }

        public ApiServiceResponse(HttpResponse response) {
            if (response == null) return;

            this.contentType = String.isBlank(response.getHeader(HEADER_CONTENT_TYPE)) ? response.getHeader(HEADER_CONTENT_TYPE.toLowerCase()) : response.getHeader(HEADER_CONTENT_TYPE);
            this.statusCode = response.getStatusCode();
            this.status = response.getStatus();
            this.body = response.getBody();
        }

        /**
         * isError: If callout returned an error
         *
         * @return
         */
        public Boolean isError() {
            return this.statusCode > 299 &&
                    !this.ignoreError;
        }

        /**
         * ignoreError : Bypass throwing ApiServiceException
         *
         * @param ignore
         */
        public void ignoreError(Boolean ignore) {
            this.ignoreError = ignore;
        }
    }

    public class InvalidParameterException extends Exception {
        public InvalidParameterException(String field, String value) {
            this(String.format('Invalid value:{0} for field: {1}', new List<String>{
                    field, value
            }));
        }
    }

    public class ApiServiceException extends Exception {
        private ApiServiceResponse response;

        public ApiServiceException(ApiServiceResponse response) {
            this(String.format('Http response returned status code:{0}, with status: {1} and body: {2}', new List<String>{
                    String.valueOf(response.statusCode), response.status, response.body
            }));

            this.response = response;
        }
    }
}