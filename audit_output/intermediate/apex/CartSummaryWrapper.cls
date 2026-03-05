/*
==========================================
    Title: CartSummaryWrapper
    Purpose: Wrapper class to store cart
        summary.
    Author: Clay Phillips
    Date: 08/24/2020 
==========================================
*/

public with sharing class CartSummaryWrapper{
    @AuraEnabled
    public String cartId{get;set;}

    @AuraEnabled
    public List<CartProductWrapper> cartItems{get;set;}
}