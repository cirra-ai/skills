public with sharing class MockarooHelperFactory {
	
	public static IMockarooHelper getIMockarooHelper(){
		return new WaveCsvDataRetriever();
	}
}