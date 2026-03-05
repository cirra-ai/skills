public with sharing class Sdo_Scom_Auction_Service {
    public static List<SDO_SCOM_Auction__c> getAuctionDetailsByProductWebStore(List<Id> productIds, Id webStoreId, List<String> status) {
        List<SDO_SCOM_Auction__c> auctionList = [
            SELECT Id, Starting_Bid_Price__c, Start_Date_Time__c, End_Date_Time__c, Product__c, Web_Store__c, Status__c
            FROM SDO_SCOM_Auction__c 
            WHERE Product__c IN :productIds AND Web_Store__c = :webStoreId AND Status__c IN :status
            ORDER BY End_Date_Time__c DESC Nulls Last LIMIT 1
        ];
        
        return auctionList;
    }

    public static List<SDO_SCOM_Auction__c> getAuctionById(Id auction) {
        Id auctionId = (Id) auction;
        return [
            SELECT Id, Start_Date_Time__c, End_Date_Time__c, Starting_Bid_Price__c, Status__c, Product__c, Web_Store__c
            FROM SDO_SCOM_Auction__c
            WHERE Id = :auctionId
        ];
    }

    public static List<SDO_SCOM_Auction_Bid__c> getHighestBidForAuction(Id auctionId) {
        return [
            SELECT Account__c, Auction__c, Bid_Amount__c, Id, Product__c, User__c
            FROM SDO_SCOM_Auction_Bid__c
            WHERE Auction__c = :auctionId
            ORDER BY Bid_Amount__c DESC Nulls Last
            LIMIT 1
        ];
    }

    @AuraEnabled
    public static List<SDO_SCOM_Auction_Bid__c> getAuctionBids(String auction) {
        Id auctionId = (Id) auction;
        List<SDO_SCOM_Auction_Bid__c> auctionBidList = [
            SELECT Id, Bid_Amount__c, Account__c, User__c, Auction__c
            FROM SDO_SCOM_Auction_Bid__c
            WHERE Auction__c = :auctionId
        ];
        return auctionBidList;
    }

    @AuraEnabled
    public static Map<String, Object> getProductAuctionDetails(Map<String, Object> request) {
        System.debug('Request received: ' + request);
        
        Id productId = (Id) request.get('productId');
        Id webStoreId = (Id) request.get('webStoreId');

        List<Id> productIds = new List<Id>{productId};
        List<String> status = new List<String>{'Pending', 'Active', 'Closed'};
        List<SDO_SCOM_Auction__c> auctions = getAuctionDetailsByProductWebStore(productIds, webStoreId, status);
        
        if (auctions.size() == 0) {
            return null;
        }

        SDO_SCOM_Auction__c auction = auctions[0];
        List<SDO_SCOM_Auction_Bid__c> auctionBids = getAuctionBids(auction.Id);

        Map<String, Object> response = new Map<String, Object>();
        response.put('auction', auction);
        response.put('auctionBids', auctionBids);

        return response;
    }

    @AuraEnabled
    public static Object addAuctionBid(Map<String, Object> request) {
        System.debug('Request bid: ' + request);
        
        Id accountId = (Id) request.get('Account__c');
        Id auctionId = (Id) request.get('Auction__c');
        Id productId = (Id) request.get('Product__c');
        Id userId = (Id) request.get('User__c');
        String amount = (String) request.get('Bid_Amount__c');
        Decimal bidAmount = Decimal.valueOf(amount);

        Boolean isNotValid = accountId == null || auctionId == null || productId == null || userId == null || bidAmount == null;
        if (isNotValid) {
            throw new AuraHandledException('Please provide all required information');
        }

        List<SDO_SCOM_Auction__c> auctions = getAuctionById(auctionId);
        if(auctions.size() == 0) {
            throw new AuraHandledException('No auctions found!');
        }
        SDO_SCOM_Auction__c auction = auctions.get(0);
        String status = auction.get('Status__c').toString();
        if(status == 'Pending') {
            throw new AuraHandledException('Auction is not started yet!');
        }

        if(status == 'Closed') {
            throw new AuraHandledException('Auction is closed!');
        }

        List<SDO_SCOM_Auction_Bid__c> bids = getHighestBidForAuction(auctionId);
        if(bids.size() == 0) {
            if(bidAmount < (Decimal)auction.get('Starting_Bid_Price__c')) {
                throw new AuraHandledException('Bid amount should be greater than starting bid!');
            }
        } else {
            SDO_SCOM_Auction_Bid__c highestBid = bids.get(0);
            if(bidAmount < (Decimal)highestBid.get('Bid_Amount__c')) {
                throw new AuraHandledException('Bid amount should be greater than last bid! Please refresh page and check!');
            }
        }

        SDO_SCOM_Auction_Bid__c bid = new SDO_SCOM_Auction_Bid__c();
        bid.Bid_Amount__c = bidAmount;
        bid.Account__c = accountId;
        bid.Auction__c = auctionId;
        bid.Product__c = productId;
        bid.User__c = userId;

        try {
            insert bid;
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
        return bid;
    }

    public static Map<Id, Decimal> getAuctionProductsPrices(List<Id> productIds, Id webStoreId, Id accountId) {
        List<String> status = new List<String>{'Closed'};
        List<SDO_SCOM_Auction__c> auctionList = getAuctionDetailsByProductWebStore(productIds, webStoreId, status);
        Map<Id, Decimal> productPrices = new Map<Id, Decimal>();
        for(Integer i = 0; i < auctionList.size(); i++) {
            SDO_SCOM_Auction__c auction = auctionList.get(i);
            Id auctionId = auction.get('Id').toString();
            List<SDO_SCOM_Auction_Bid__c> auctionBids = getHighestBidForAuction(auctionId);
            System.debug(auctionBids);
            if(auctionBids.size() != 0) {
                SDO_SCOM_Auction_Bid__c highestBid = auctionBids[0];
                Id bidAccount = highestBid.get('Account__c').toString();
                System.debug('Account Ids' + bidAccount + ' == ' + accountId + ' ');
                if(bidAccount == accountId) {
                    Id productId = auction.get('Product__c').toString();
                    productPrices.put(productId, (Decimal) highestBid.get('Bid_Amount__c'));
                }
            }
        }
        return productPrices;
    }

    @future
    public static void addAuctionProductToUserCart(Id auctionId) {
        System.debug('Add auction product to user cart - auction id: ' + auctionId);
        try {
            // Get Auction Details
            List<SDO_SCOM_Auction__c> auctions = getAuctionById(auctionId);
            if(auctions.size() == 0) {
                System.debug('Add auction product to user cart - No Auction found for Auction Id: ' + auctionId);
                return;
            }
            SDO_SCOM_Auction__c auction = auctions.get(0);
            System.debug('Add auction product to user cart - auction details: ' + auction);

            // Get Bid Details
            List<SDO_SCOM_Auction_Bid__c> bids = getHighestBidForAuction(auctionId);
            if(bids.size() == 0) {
                System.debug('Add auction product to user cart - No Bids found for Auction Id: ' + auctionId);
                return;
            }
            SDO_SCOM_Auction_Bid__c heighestBid = bids.get(0);
            System.debug('Add auction product to user cart - bid details: ' + heighestBid);
            
            String productId = auction.get('Product__c').toString();
            String webStoreId = auction.get('Web_Store__c').toString();
            String accountId = heighestBid.get('Account__c').toString();
            String userId = heighestBid.get('User__c').toString();
            Sdo_Scom_Auction_Cart_Service.addItemToCart(webStoreId, accountId, userId, productId);
        } catch (Exception e) {
            System.debug('An exception occurred during add auction product to user cart: ' + e.getMessage());
        }
    }    
}