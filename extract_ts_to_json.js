const fs = require('fs');
const tsConfig = require('typescript');

// To execute TS file that uses ES modules, we can read it, strip the export keywords, and eval.
const tsFilePath = "C:\\BISMALLAH BIZSYSTEMS INSHA'ALLAH\\BISMALLAH_BizMarketing_New_INSHAALLAH\\Week 1-4 Social Media Campaign Plan Development\\Campaign_Post_Website\\campaignData.ts";

let tsCode = fs.readFileSync(tsFilePath, 'utf8');

// Quick and dirty transpilation by removing types. 
// A safer approach: transpile using tsc programmatically
let jsCode = tsConfig.transpile(tsCode);

// Evaluate the exported variables
const sandbox = {};
try {
    eval(`
        const exports = {};
        ${jsCode};
        Object.assign(sandbox, exports);
    `);
    
    // Dump to JSON
    fs.writeFileSync('./bizmarketing/campaign_data_export.json', JSON.stringify({
        weeks: sandbox.campaignWeeks,
        pillars: sandbox.pillars
    }, null, 2));
    
    console.log("Successfully dumped campaign data to JSON!");
} catch (e) {
    console.error("Error evaluating TS content:", e);
}
