/*
==========================================
    Title: CartProductWrapper
    Purpose: Wrapper class to store cart
        products.
    Author: Clay Phillips
    Date: 08/20/2020 
==========================================
*/

public with sharing class CartProductWrapper{
    @AuraEnabled
    public String productId{get;set;}

    @AuraEnabled
    public Integer quantity{get;set;}

    @AuraEnabled
    public String errorMessage{get;set;}

    @AuraEnabled
    public String requestStatus{get;set;}
}