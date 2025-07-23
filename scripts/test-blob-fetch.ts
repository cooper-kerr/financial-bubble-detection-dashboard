import { config } from 'dotenv';

// Load environment variables
config({ path: '.env.local' });

// Test fetching data from blob storage
async function testBlobFetch() {
  const testUrl = "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_1996to2023.json";
  
  console.log('🧪 Testing blob fetch...');
  console.log('📡 URL:', testUrl);
  
  try {
    const response = await fetch(testUrl);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    console.log('✅ Fetch successful!');
    console.log('📊 Data structure:');
    console.log('  - Stock code:', data.metadata?.stockcode);
    console.log('  - Time series points:', data.time_series_data?.length);
    console.log('  - Date range:', data.metadata?.time_series_start_date, 'to', data.metadata?.time_series_end_date);
    
    // Test a sample data point
    if (data.time_series_data && data.time_series_data.length > 0) {
      const samplePoint = data.time_series_data[0];
      console.log('📈 Sample data point:');
      console.log('  - Date:', samplePoint.date);
      console.log('  - Stock price:', samplePoint.stock_prices?.adjusted);
      console.log('  - Has bubble estimates:', !!samplePoint.bubble_estimates);
    }
    
    return true;
  } catch (error) {
    console.error('❌ Fetch failed:', error);
    return false;
  }
}

testBlobFetch().then(success => {
  if (success) {
    console.log('\n🎉 Vercel Blob Storage integration is working correctly!');
  } else {
    console.log('\n💥 There seems to be an issue with the blob storage setup.');
  }
});
