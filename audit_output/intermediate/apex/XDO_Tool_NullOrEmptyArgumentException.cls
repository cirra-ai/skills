public with sharing class XDO_Tool_NullOrEmptyArgumentException extends Exception {
    public XDO_Tool_NullOrEmptyArgumentException(String field, String arg) {
        setMessage('The field "' + field + '" cannot be empty.');
    }
}