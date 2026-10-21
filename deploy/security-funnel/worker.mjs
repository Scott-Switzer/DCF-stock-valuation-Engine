// Private staging reconciliation. No upstream providers or raw archive reads.
import {connectionRoute,CONNECTED} from './connections.mjs';
const BASE = 'staging/security-funnel/2026-10-20/9beaa712e71650a2/';
const OUT = BASE + 'reconciled-2026-10-21-v1/';
const RELEASE = 'b39a670bad0670449256e59d38bf6b9600503449baded29c25e41d5fb368c6bb';
const ASOF = '2026-10-21';
const IMPLEMENTATION = 'cloud-reconciliation-v2-packet-qualified';
const enc = new TextEncoder();
const hex = b => Array.from(new Uint8Array(b), x => x.toString(16).padStart(2,'0')).join('');
const sha = async s => hex(await crypto.subtle.digest('SHA-256',enc.encode(s)));
const fail = code => { throw new Error(code); };
async function read(env,key,max=16*1048576,digest=null) {
  const obj = await env.DATA.get(key);
  if (!obj || obj.size > max) fail('OBJECT_MISSING_OR_OVERSIZE');
  const raw = await obj.text();
  if (digest && await sha(raw) !== digest) fail('OBJECT_HASH_MISMATCH');
  return JSON.parse(raw);
}
async function put(env,key,value) {
  const raw=JSON.stringify(value);
  await env.DATA.put(key,raw,{httpMetadata:{contentType:'application/json'},customMetadata:{sha256:await sha(raw)}});
}
async function signedRead(env,key) {
  const scope=await sha('zion-engine-derived-cache-scope-v1\0'+env.TOKEN);
  const scoped='gold/cache-scopes/'+scope+'/'+key.slice(5);
  const obj=await env.DATA.get(scoped);
  if (!obj || obj.size>16*1048576) fail('SIGNED_CACHE_UNAVAILABLE');
  const raw=await obj.text();
  // Verify exact persisted UTF-8 bytes, avoiding numeric/Unicode reserialization.
  const match=/^\{"mac":"([a-f0-9]{64})","value":/.exec(raw);
  if (!match || !raw.endsWith('}')) fail('CACHE_ENVELOPE_INVALID');
  const body=raw.slice(match[0].length,-1);
  const k=await crypto.subtle.importKey('raw',enc.encode(env.TOKEN),{name:'HMAC',hash:'SHA-256'},false,['verify']);
  const sig=Uint8Array.from(match[1].match(/../g), x=>parseInt(x,16));
  if (!await crypto.subtle.verify('HMAC',k,sig,enc.encode(body))) fail('CACHE_MAC_INVALID');
  return JSON.parse(body);
}
export function freshness(date,max) {
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return {status:'UNKNOWN',observed_through:date||null,policy_max_age_days:max};
  const t=Date.parse(date+'T00:00:00Z');
  if (!Number.isFinite(t) || new Date(t).toISOString().slice(0,10)!==date) return {status:'INVALID',observed_through:date,policy_max_age_days:max};
  const age=(Date.parse(ASOF+'T00:00:00Z')-t)/86400000;
  return {status:age<0?'FUTURE':age>max?'STALE':'WITHIN_POLICY',age_days:age,observed_through:date,policy_max_age_days:max};
}
function add(a,x) { if (!a.includes(x)) a.push(x); }
function reasons(row) {
  return [...new Set(['identity','adjusted_prices','financials','valuation'].flatMap(k=>row[k]?.blockers||[]))];
}
function cite(source) {
  const r=source?.source_record||{};
  const acc=r.accn||source?.accession;
  const cik=source?.cik;
  return {source_observation_id:source?.source_observation_id, accession:acc||null,
    url:acc&&cik?`https://www.sec.gov/Archives/edgar/data/${Number(cik)}/${acc.replaceAll('-','')}/`:
      cik?`https://www.sec.gov/edgar/browse/?CIK=${cik}`:null};
}
async function initialize(env) {
  const ledger=await read(env,BASE+'preserved/cloudflare-receipts/ledger.json');
  const jobs=await read(env,BASE+'job-status.json');
  const campaign=await read(env,BASE+'campaign.json',1048576,env.CAMPAIGN_SHA256);
  if (ledger.securities.length!==2629 || new Set(ledger.securities.map(r=>r.symbol)).size!==2629 ||
      campaign.source_release_id!==RELEASE) fail('FROZEN_UNIVERSE_OR_RELEASE_CHANGED');
  const tasks={};
  for (const j of jobs) {
    if (j.release_id!==RELEASE) fail('JOB_RELEASE_CHANGED');
    for (const c of j.companies) {
      if (tasks[c.cik] && tasks[c.cik].query_fingerprint!==c.query_fingerprint) fail('DUPLICATE_ISSUER_JOB_CONFLICT');
      tasks[c.cik]={...c,job_id:j.job_id};
    }
  }
  if (Object.keys(tasks).length!==1909 || Object.values(tasks).some(t=>t.status!=='COMPLETE')) fail('CLOUD_JOBS_NOT_COMPLETE');
  const packets=await read(env,'control/valuation/CURRENT.json',524288);
  if (packets.schema_version!=='ppe-valuation-index-v1') fail('VALUATION_INDEX_INVALID');
  const inputHash=await sha(JSON.stringify({ledger,jobs,packets,campaign,asof:ASOF,implementation:IMPLEMENTATION}));
  const existing=await env.DATA.get(OUT+'input.json');
  if (existing && (await existing.json()).input_sha256!==inputHash) fail('RECONCILIATION_INPUT_CHANGED');
  const batches=Math.ceil(ledger.securities.length/20);
  await put(env,OUT+'symbol-batches.json',Object.fromEntries(ledger.securities.map((r,i)=>[r.symbol,Math.floor(i/20)])));
  for (let n=0;n<batches;n++) {
    const rows=ledger.securities.slice(n*20,n*20+20).map(row=>({row,task:tasks[row.identity.cik]||null,packet:packets.companies[row.symbol]||null,
      quarantine:campaign.skipped.find(c=>c.cik===row.identity.cik)||null}));
    await put(env,OUT+`inputs/${n}.json`,{input_sha256:inputHash,rows});
  }
  const result={schema_version:'cloud-security-reconciliation-v1',asof:ASOF,input_sha256:inputHash,
    source_release_id:RELEASE,universe_release_id:ledger.universe_release_id,securities:2629,batches,
    cloud_completed_issuers:1909,cloud_covered_symbols:1929,valuation_packet_index_sha256:await sha(JSON.stringify(packets)),
    original_policy:ledger.policy,output_prefix:OUT};
  await put(env,OUT+'input.json',result);
  return result;
}
async function checkPacket(env,ref,row) {
  if (!ref || !/^gold\/valuation\/releases\/[a-f0-9]{64}\/companies\/[A-Z0-9.-]+\.json$/.test(ref.key)||! /^[a-f0-9]{64}$/.test(ref.sha256)) return null;
  const p=await read(env,ref.key,131072,ref.sha256);
  if (p.schema_version!=='ppe-valuation-packet-v1'||p.ticker!==row.symbol||p.cik!==row.identity.cik) fail('VALUATION_PACKET_IDENTITY_MISMATCH');
  const cutoff=freshness(p.cutoff_date,45);
  if (['UNKNOWN','INVALID','FUTURE'].includes(cutoff.status)) fail('VALUATION_PACKET_CUTOFF_INVALID');
  if (!Array.isArray(p.historical)||!p.historical.length) fail('VALUATION_PACKET_HISTORY_EMPTY');
  const fields=[];const missing=[];
  for (const period of p.historical||[]) for (const [name,v] of Object.entries(period.fields||{})) {
    if (v===null) {add(missing,name);continue;}
    if (!v || typeof v.value!=='number' || !Number.isFinite(v.value) || !v.unit || !v.provenance ||
        freshness(v.available_at?.slice(0,10),100000).status!=='WITHIN_POLICY') fail('VALUATION_PACKET_FIELD_INVALID');
    add(fields,name);
  }
  if (!fields.length) fail('VALUATION_PACKET_USABLE_FIELDS_EMPTY');
  const periods=p.historical.flatMap(h=>Object.values(h.fields||{}).filter(Boolean).map(v=>v.period_end)).filter(Boolean).sort();
  return {status:'SOURCE_PACKET_VERIFIED',key:ref.key,sha256:ref.sha256,cutoff_date:p.cutoff_date,
    cutoff_freshness:cutoff,latest_period_freshness:freshness(periods.at(-1),550),
    fields_available:fields,missing_fields:missing,method_suitability:'NOT_VERIFIED',
    qualification:'NONEMPTY_SOURCE_INPUT_PACKET;NOT_METHOD_COMPLETE_OR_EXECUTED_VALUATION'};
}
async function processRow(env,item) {
  const {row,task}=item;
  row.assessed_asof=ASOF;
  row.identity.alias_freshness={status:'UNKNOWN',reason:'ALIAS_SNAPSHOT_DATE_UNRECORDED'};
  row.adjusted_prices.freshness=freshness(row.adjusted_prices.date_max,7);
  row.adjusted_prices.blockers=row.adjusted_prices.blockers.filter(b=>!b.startsWith('PRICE_FRESHNESS_'));
  if (row.adjusted_prices.freshness.status!=='WITHIN_POLICY') add(row.adjusted_prices.blockers,'PRICE_FRESHNESS_'+row.adjusted_prices.freshness.status);
  row.adjusted_prices.validation={status:'CHECKED_BLOCKED',source:'FROZEN_STORED_PRICE_METADATA',
    raw_prices_present:row.adjusted_prices.stored_rows>0,adjustment_evidence_verified:false,dated_identity_verified:false};
  row.financials.source_freshness=freshness('2026-09-24',45);
  row.financials.freshness=freshness(row.financials.latest_period_end,550);
  row.financials.adapter_status=row.financials.status;
  const brief={symbol:row.symbol,cik:row.identity.cik||null,asof:ASOF,source_cutoff:'2026-09-24',
    source_release_id:RELEASE,latest_annual_observations:[],citations:[],qualification:'CITED_SOURCE_RESEARCH_AND_GAPS;NO_INVESTMENT_RECOMMENDATION'};
  if (task) {
    if (!/^[a-f0-9]{64}$/.test(task.query_fingerprint)) fail('INVALID_QUERY_FINGERPRINT');
    const queryKey=`gold/sec-engine/releases/${RELEASE}/queries/${task.query_fingerprint}.json`;
    const data=await signedRead(env,queryKey);
    if (data.cik!==row.identity.cik || data.provenance?.release_id!==RELEASE || data.frequency!=='annual') fail('QUERY_CONTEXT_MISMATCH');
    const obs=data.observations||[];
    if (obs.length!==task.total_observations || (data.coverage_gaps||[]).length!==task.total_coverage_gaps) fail('QUERY_COUNTS_CHANGED');
    for (const o of obs) {
      if (typeof o.value_decimal!=='string'||!o.source_observation_ids?.length||
        o.source_observation_ids.some(s=>!data.source_records?.[s])) fail('QUERY_LINEAGE_INCOMPLETE');
    }
    const latest={};
    for (const o of obs) if (!latest[o.metric]||o.period_end>latest[o.metric].period_end) latest[o.metric]=o;
    const end=obs.map(o=>o.period_end).sort().at(-1)||null;
    row.financials.cloud={status:obs.length?'CLOUD_HISTORY_VERIFIED':'CLOUD_HISTORY_EMPTY',job_id:task.job_id,
      query_fingerprint:task.query_fingerprint,history_url:task.history_url,observations:obs.length,
      coverage_gaps:(data.coverage_gaps||[]).length,source_cutoff:'2026-09-24',release_id:RELEASE,
      annual_metrics_available:Object.keys(latest).sort(),latest_period_end:end,
      coverage_gap_reasons:[...new Set((data.coverage_gaps||[]).map(g=>g.reason))],
      qualification:'HMAC_VERIFIED_STORED_QUERY;NOT_DCF_ADAPTER_OR_PRICE_JOIN_CERTIFICATION'};
    row.financials.status=row.financials.cloud.status;
    row.financials.latest_period_end=end;
    row.financials.freshness=freshness(end,550);
    brief.latest_annual_observations=Object.values(latest).map(o=>({metric:o.metric,value_decimal:o.value_decimal,
      unit:o.unit,period_end:o.period_end,available_at:o.available_at,source_observation_ids:o.source_observation_ids}));
    const ids=[...new Set(Object.values(latest).flatMap(o=>o.source_observation_ids))];
    brief.citations=ids.map(id=>({...cite({...data.source_records[id],cik:row.identity.cik}),
      query_fingerprint:task.query_fingerprint,source_release_id:RELEASE}));
    row.source_references.push({kind:'cloud_verified_sec_history',release_id:RELEASE,query_fingerprint:task.query_fingerprint,job_id:task.job_id});
  } else {
    row.financials.cloud={status:'NOT_IN_COMPLETED_CLOUD_COHORT',reason:item.quarantine?.reason||'NO_MATERIALIZED_MATCHED_ISSUER',quarantine_status:item.quarantine?.status||null};
    add(row.financials.blockers,row.financials.cloud.reason);
  }
  let packet=null;
  try { packet=await checkPacket(env,item.packet,row); }
  catch(e) { row.valuation.packet_error=e.message;add(row.valuation.blockers,e.message); }
  row.valuation.packet=packet||{status:'NO_STORED_PACKET'};
  // The source-input packet is not a model result. Never fill economic assumptions.
  row.valuation.blockers=[...new Set([...row.valuation.blockers,...row.adjusted_prices.blockers])];
  add(row.valuation.blockers,'MODEL_EXECUTION_REQUIRED');
  if (!packet) add(row.valuation.blockers,'VALUATION_ADAPTER_PACKET_REQUIRED');
  if (row.financials.freshness.status!=='WITHIN_POLICY') add(row.valuation.blockers,'FINANCIAL_PERIOD_'+row.financials.freshness.status);
  row.valuation.status='CHECKED_BLOCKED';row.valuation.completed=false;
  row.valuation.next_action=packet?'SUPPLY_DATED_ASSUMPTIONS_AND_REPAIR_PRICE_IDENTITY_GATES':'BUILD_SOURCE_QUALIFIED_METHOD_SPECIFIC_ADAPTER';
  brief.identity=row.identity.status;brief.financials=row.financials.cloud;
  brief.price_check=row.adjusted_prices.validation;brief.price_freshness=row.adjusted_prices.freshness;
  brief.financial_freshness=row.financials.freshness;brief.source_freshness=row.financials.source_freshness;
  brief.valuation=row.valuation;brief.gaps=reasons(row);
  if (!brief.citations.length) brief.citations=row.source_references;
  row.research_brief={status:row.financials.cloud.status==='CLOUD_HISTORY_VERIFIED'?'CLOUD_CITED_FINANCIAL_BRIEF_AVAILABLE':'CLOUD_CITED_GAP_BRIEF_AVAILABLE',
    blockers:['FULL_WORKFLOW_NOT_VERIFIED'],qualification:brief.qualification};
  return {row,brief};
}
async function batch(env,n) {
  const input=await read(env,OUT+'input.json');
  if (!Number.isInteger(n)||n<0||n>=input.batches) fail('INVALID_BATCH');
  const done=await env.DATA.get(OUT+`batches/${n}.json`);
  if (done) {
    const d=await done.json();if (d.input_sha256!==input.input_sha256) fail('CHECKPOINT_PIN_CHANGED');
    if (d.packet_policy_version!==IMPLEMENTATION) {
      // Upgrade only small packet checks. Never reread completed financial queries.
      const originals=await read(env,OUT+`inputs/${n}.json`);
      const briefs=await read(env,OUT+`briefs/${n}.json`);
      for (const row of d.rows) {
        if (row.reconciliation_error) continue;
        const ref=originals.rows.find(i=>i.row.symbol===row.symbol)?.packet;
        try {row.valuation.packet=await checkPacket(env,ref,row)||{status:'NO_STORED_PACKET'};}
        catch(e) {row.valuation.packet={status:'PACKET_REJECTED',reason:e.message};add(row.valuation.blockers,e.message);}
        if (row.valuation.packet.status!=='SOURCE_PACKET_VERIFIED') {
          add(row.valuation.blockers,'VALUATION_ADAPTER_PACKET_REQUIRED');
          row.valuation.next_action='BUILD_SOURCE_QUALIFIED_METHOD_SPECIFIC_ADAPTER';
        }
        const brief=briefs.briefs.find(b=>b.symbol===row.symbol);
        if (brief) {brief.valuation=row.valuation;brief.gaps=reasons(row);}
      }
      d.packet_policy_version=IMPLEMENTATION;
      await put(env,OUT+`briefs/${n}.json`,briefs);
      await put(env,OUT+`batches/${n}.json`,d);
    }
    return {batch:n,securities:d.rows.length,reused:true,packet_policy_version:d.packet_policy_version};
  }
  const part=await read(env,OUT+`inputs/${n}.json`);
  if (part.input_sha256!==input.input_sha256) fail('INPUT_SHARD_CHANGED');
  const rows=[],briefs=[],errors=[];
  for (const item of part.rows) {
    const original=structuredClone(item.row);
    try {const r=await processRow(env,item);rows.push(r.row);briefs.push(r.brief);}
    catch(e) {const r=original;r.reconciliation_error=e.message;r.research_brief={status:'CLOUD_RECONCILIATION_FAILED',blockers:[e.message]};rows.push(r);errors.push({symbol:r.symbol,reason:e.message});}
  }
  await put(env,OUT+`briefs/${n}.json`,{input_sha256:input.input_sha256,briefs,errors});
  await put(env,OUT+`batches/${n}.json`,{input_sha256:input.input_sha256,packet_policy_version:IMPLEMENTATION,rows,errors});
  return {batch:n,securities:rows.length,briefs:briefs.length,errors};
}
const ACTIONS={
  CROSS_SOURCE_DATED_IDENTITY_REQUIRED:'Build dated CIK/security/class/provider crosswalk; unique ticker candidates alone are insufficient.',
  ADJUSTMENT_EVIDENCE_MISSING:'Validate stored CRSP split and distribution factors by PERMNO before cross-provider joins.',
  PRICE_FRESHNESS_STALE:'Use existing ongoing collector and stored recent bars after identity and adjustment semantics are validated.',
  DATED_ASSUMPTIONS_REQUIRED:'Version method-specific forecast, discount rate, and terminal assumptions with as-of dates.',
  MODEL_EXECUTION_REQUIRED:'Run the existing model only after inputs and assumptions pass their gates.',
  VALUATION_ADAPTER_PACKET_REQUIRED:'Build method-specific packets from verified cloud history; route non-revenue issuers separately.'
};
async function finalize(env) {
  const input=await read(env,OUT+'input.json');
  await read(env,BASE+'campaign.json',1048576,env.CAMPAIGN_SHA256);
  const effectivePin=await sha(JSON.stringify({input_sha256:input.input_sha256,campaign_sha256:env.CAMPAIGN_SHA256,implementation:IMPLEMENTATION,asof:ASOF}));
  const securities=[],groups={},stages={},errors=[];
  let financialBriefs=0,packets=0,verifiedHistory=0;
  for (let n=0;n<input.batches;n++) {
    const p=await read(env,OUT+`batches/${n}.json`);
    if (p.input_sha256!==input.input_sha256) fail('BATCH_PIN_CHANGED');
    if (p.packet_policy_version!==IMPLEMENTATION) fail('PACKET_POLICY_UPGRADE_REQUIRED');
    const empty=p.rows.filter(r=>r.financials.cloud?.status==='CLOUD_HISTORY_EMPTY');
    if (empty.length) {
      const bundle=await read(env,OUT+`briefs/${n}.json`);
      for (const row of empty) {
        row.research_brief.status='CLOUD_CITED_GAP_BRIEF_AVAILABLE';
        add(row.financials.blockers,'CLOUD_ANNUAL_QUERY_EMPTY');
        const b=bundle.briefs.find(b=>b.symbol===row.symbol);
        if (b) {b.qualification='CITED_SOURCE_GAP_BRIEF;NO_USABLE_ANNUAL_OBSERVATIONS';b.gaps=reasons(row);}
      }
      await put(env,OUT+`batches/${n}.json`,p);
      await put(env,OUT+`briefs/${n}.json`,bundle);
    }
    securities.push(...p.rows);errors.push(...p.errors);
  }
  if (securities.length!==2629||new Set(securities.map(r=>r.symbol)).size!==2629) fail('UNIVERSE_ACCOUNTING_FAILED');
  await put(env,OUT+'symbol-batches.json',Object.fromEntries(securities.map((r,i)=>[r.symbol,Math.floor(i/20)])));
  for (const row of securities) {
    for (const k of ['identity','adjusted_prices','financials','valuation','research_brief']) {
      stages[k]??={};stages[k][row[k].status]=(stages[k][row[k].status]||0)+1;
    }
    if (row.financials.cloud?.status==='CLOUD_HISTORY_VERIFIED') verifiedHistory++;
    if (row.valuation.packet?.status==='SOURCE_PACKET_VERIFIED') packets++;
    if (row.research_brief.status==='CLOUD_CITED_FINANCIAL_BRIEF_AVAILABLE') financialBriefs++;
    for (const reason of reasons(row)) {groups[reason]??=[];groups[reason].push(row.symbol);}
  }
  const repairs=Object.entries(groups).map(([blocker,symbols])=>({blocker,affected_securities:symbols.length,symbols,
    action:ACTIONS[blocker]||'Inspect pinned source gap and repair once for this cohort.',
    unlock_qualification:'REMOVES_ONE_GATE;NOT_A_GUARANTEED_FULL_WORKFLOW_UNLOCK'}))
    .sort((a,b)=>b.affected_securities-a.affected_securities||a.blocker.localeCompare(b.blocker));
  const summary={status:errors.length?'RECONCILED_WITH_EXPLICIT_FAILURES':'RECONCILED',asof:ASOF,accounted:2629,
    cloud_verified_financial_symbols:verifiedHistory,cloud_cited_financial_briefs:financialBriefs,
    source_packets_verified:packets,full_workflow_verified:0,executed_valuations:0,reconciliation_failures:errors.length,
    stages,top_repairs:repairs.slice(0,12).map(({symbols,...r})=>r),laptop_normalizations:0,raw_archive_downloads:0,
    production_writes:0,output_prefix:OUT,input_sha256:input.input_sha256,
    effective_input_sha256:effectivePin,campaign_sha256:env.CAMPAIGN_SHA256,implementation:IMPLEMENTATION};
  await put(env,OUT+'ledger.json',{...input,summary,securities,repair_queue:repairs,errors});
  await put(env,OUT+'repair-queue.json',repairs);
  await put(env,OUT+'summary.json',summary);
  const report=`# Cloud security readiness — ${ASOF}\n\nAccounted: 2,629 / 2,629. Cloud histories verified: ${verifiedHistory}. Cited financial briefs: ${financialBriefs}. Existing valuation source packets verified: ${packets}. Reconciliation failures: ${errors.length}.\n\nNo complete valuations or adjusted-price series are certified. Each security retains explicit price, dated identity, source, adapter, and assumption gates. Briefs are source research, not recommendations. Source cutoff: 2026-09-24; source age: 27 days; 45-day research policy. Alias snapshot freshness remains unknown.\n\n## Shared repairs by affected symbols\n\n${repairs.map(r=>`- ${r.blocker}: ${r.affected_securities}. ${r.action}`).join('\n')}\n\nCounts overlap: each repair removes one gate, not necessarily all workflow blockers. All processing and artifacts are private in Cloudflare. No raw archives downloaded, no laptop normalization, no production pointer changes.\n`;
  await env.DATA.put(OUT+'REPORT.md',report,{httpMetadata:{contentType:'text/markdown'}});
  return summary;
}
export default {
  async fetch(request,env) {
    if (!env.TOKEN || request.headers.get('Authorization')!=='Bearer '+env.TOKEN) return new Response('Unauthorized',{status:401});
    const u=new URL(request.url);
    try {
      let result;
      if(request.method==='POST'&&u.pathname.startsWith('/connect/')) result=await connectionRoute(env,u.pathname,Number(u.searchParams.get('n')));
      else if (request.method==='POST'&&u.pathname==='/initialize') result=await initialize(env);
      else if (request.method==='POST'&&u.pathname==='/batch'&&/^\d+$/.test(u.searchParams.get('n')||'')) result=await batch(env,Number(u.searchParams.get('n')));
      else if (request.method==='POST'&&u.pathname==='/finalize') result=await finalize(env);
      else if (request.method==='GET'&&u.pathname==='/status') {
        result=await read(env,OUT+'summary.json');
        const connected=await env.DATA.get(CONNECTED+'summary.json');
        if(connected){
          result.connections=await connected.json();result.status='CONNECTED';
          result.stages.native_identity=result.connections.stages.identity;
          result.stages.native_adjusted_history=result.connections.stages.adjusted_history;
          result.stages.recent_prices=result.connections.stages.recent_prices;
        }
      }
      else if (request.method==='POST'&&u.pathname==='/reuse') {
        const sources=await read(env,BASE+'existing-capabilities.json');
        const pointer=sources.daily_pointer;
        if (!/^gold\/daily-prices\/releases\/[a-f0-9]{64}\/data.json$/.test(pointer.data_key)) fail('DAILY_REFERENCE_INVALID');
        const daily=await read(env,pointer.data_key,8*1048576,pointer.sha256);
        const index=await read(env,OUT+'symbol-batches.json');
        const found={};
        for (const bar of daily.bars||[]) {
          const symbol=bar.provider_symbol||bar.symbol;
          if (symbol && symbol in index) found[symbol]={symbol,session:pointer.session,
            source_security_id:bar.security_id,status:'RECENT_SOURCE_PRICE_AVAILABLE',
            freshness:freshness(pointer.session,7),qualification:'SOURCE_NATIVE_AVAILABILITY;DATED_ISSUER_JOIN_AND_ADJUSTMENTS_STILL_REQUIRED'};
        }
        result={source_discovery:sources,source_price_freshness:freshness(pointer.session,7),
          recent_source_symbols:Object.keys(found).length,universe_symbols:2629,securities:Object.values(found),
          stored_payload_fields:Object.keys(daily),stored_bar_fields:Object.keys((daily.bars||[])[0]||{}),
          correction:'The frozen archive price age is not the age of all stored prices. Existing CRSP adjustments and dated identity assets must be integrated, not rebuilt.',
          adjusted_price_certifications_added:0,production_writes:0};
        await put(env,OUT+'reuse-opportunities.json',result);
      }
      else if (request.method==='GET'&&['/brief','/security'].includes(u.pathname)) {
        const symbol=u.searchParams.get('symbol')||'';
        if (!/^[A-Z0-9][A-Z0-9.-]{0,24}$/.test(symbol)) fail('INVALID_SYMBOL');
        const index=await read(env,OUT+'symbol-batches.json');
        if (!(symbol in index)) return Response.json({error:'SYMBOL_NOT_IN_FROZEN_UNIVERSE'},{status:404});
        const brief=u.pathname==='/brief';
        const connected=await env.DATA.head(CONNECTED+'summary.json');
        const part=await read(env,(connected?CONNECTED:OUT)+(brief?'briefs/':'batches/')+index[symbol]+'.json');
        result=(brief?part.briefs:part.rows).find(r=>r.symbol===symbol);
        if (!result) fail('SYMBOL_RECONCILIATION_FAILED');
      }
      else if (request.method==='GET'&&u.pathname==='/report') {
        const connected=await env.DATA.head(CONNECTED+'summary.json');
        const obj=await env.DATA.get((connected?CONNECTED:OUT)+'REPORT.md');
        if (!obj) fail('REPORT_NOT_READY');
        return new Response(obj.body,{headers:{'Content-Type':'text/markdown','Cache-Control':'private, no-store'}});
      }
      else return new Response('Not found',{status:404});
      return Response.json(result,{headers:{'Cache-Control':'private, no-store'}});
    } catch(e) {return Response.json({error:e.message},{status:422,headers:{'Cache-Control':'private, no-store'}});}
  }
};
