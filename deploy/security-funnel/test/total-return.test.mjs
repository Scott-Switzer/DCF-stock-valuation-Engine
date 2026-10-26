import {test} from 'node:test';
import assert from 'node:assert/strict';
import {totalReturnSeries,delistingFamily} from '../total-return.mjs';

const close=(date,split_adjusted_price,source_total_return,dlydelflg='N')=>({date,split_adjusted_price,source_total_return,dlydelflg,delisting_return_present:dlydelflg==='Y'&&typeof source_total_return==='number'});
const near=(a,b,tolerance=1e-9)=>assert.ok(Math.abs(a-b)<tolerance,`${a} != ${b}`);

test('chaining CRSP RET exceeds split-adjusted price growth by the distributions',()=>{
 // 100 -> 105 -> 110 split-adjusted (10%), with returns that chain to 15%.
 const rows=[close('2020-01-02',100,null),close('2020-06-30',105,0.07),close('2020-12-31',110,1.15/1.07-1)];
 const result=totalReturnSeries(rows,{from:'2020-01-02',to:'2020-12-31'});
 near(result.summary.total_return,0.15);
 near(result.summary.price_growth,0.10);
 near(result.summary.dividend_contribution,1.15/1.10-1);
 assert.equal(result.summary.total_return_complete,true);
 assert.equal(result.summary.total_return_is_upper_bound,false);
 assert.equal(result.summary.sessions,3);
 assert.equal(result.summary.returns_applied,2);
 assert.equal(result.delisting.status,'NO_DELISTING_RECORD');
 assert.equal(result.segments.length,1);
 near(result.segments[0].total_return,0.15);
 // The first close's own return describes the move into it and is not applied.
 assert.equal(result.summary.returns_applied,rows.length-1);
});

test('a reported delisting return is applied once, never twice',()=>{
 const rows=[close('2010-01-04',20,null),close('2010-11-30',20.95,0.000956),close('2010-12-01',null,0.003628,'Y')];
 const record={date:'2010-11-30',code:233,dlret:0.003628,dlretx:0.003628};
 const result=totalReturnSeries(rows,{from:'2010-01-04',to:'2010-12-01',delisting:record});
 near(result.summary.total_return,(1.000956*1.003628)-1);
 assert.equal(result.delisting.status,'DELISTING_RETURN_INCLUDED_IN_SOURCE_TOTAL_RETURN');
 assert.equal(result.delisting.treatment,'APPLIED_ONCE_BY_SOURCE_ROW');
 assert.equal(result.delisting.cross_check,'MATCH_OR_NOT_RECORDED');
 assert.equal(result.delisting.record.family,'MERGED');
 assert.equal(result.summary.total_return_is_upper_bound,false);
});

test('an unobserved delisting return stays a named bound instead of becoming zero',()=>{
 const rows=[close('2000-01-03',2,null),close('2000-11-17',1.0625,-0.15),close('2000-11-20',null,null,'Y')];
 const record={date:'2000-11-17',code:552,dlret:null,dlretx:null};
 const result=totalReturnSeries(rows,{from:'2000-01-03',to:'2000-11-20',delisting:record});
 assert.equal(result.delisting.status,'DELISTING_RETURN_NOT_OBSERVED');
 assert.equal(result.delisting.treatment,'NO_IMPUTATION_APPLIED');
 near(result.summary.total_return,-0.15);
 assert.equal(result.summary.total_return_is_upper_bound,true);
 assert.equal(result.summary.bounds.lower,-1);
 near(result.summary.bounds.upper,-0.15);
 assert.equal(result.summary.bounds.assumption,result.delisting.bounds_assumption);
 assert.equal(result.summary.missing_return_rows,1);
 assert.equal(result.gaps.length,1);
 // The price comparison cannot use the unpriced delisting row.
 assert.equal(result.summary.price_growth_end_date,'2000-11-17');
 assert.equal(result.summary.dividend_contribution,null);
});

test('an interior missing return yields segments and no cumulative claim',()=>{
 const rows=[close('2020-01-02',10,null),close('2020-02-03',11,0.1),close('2020-03-02',12,null),close('2020-03-31',13,0.08333333333333334)];
 const result=totalReturnSeries(rows,{from:'2020-01-02',to:'2020-03-31'});
 assert.equal(result.summary.total_return,null);
 assert.equal(result.summary.total_return_complete,false);
 assert.equal(result.summary.missing_return_rows,1);
 assert.equal(result.segments.length,2);
 near(result.segments[0].total_return,0.1);
 near(result.segments[1].total_return,0.08333333333333334);
 assert.equal(result.summary.dividend_contribution,null);
});

test('windows, duplicates and impossible returns fail instead of being repaired',()=>{
 const rows=[close('2020-01-02',10,null),close('2020-12-31',11,0.1)];
 assert.throws(()=>totalReturnSeries(rows,{from:'2020-01-03',to:'2020-12-31'}),/WINDOW_NOT_COVERED/);
 assert.throws(()=>totalReturnSeries([rows[0],rows[0]],{from:'2020-01-02',to:'2020-01-02'}),/STRICTLY_INCREASING/);
 assert.throws(()=>totalReturnSeries([rows[0],close('2020-12-31',11,-1.5)],{from:'2020-01-02',to:'2020-12-31'}),/OUT_OF_RANGE/);
 assert.throws(()=>totalReturnSeries([rows[0]],{from:'2020-01-02',to:'2020-01-02'}),/TWO_SESSIONS/);
});

test('delisting families separate mergers, exchanges, liquidations and drops',()=>{
 assert.equal(delistingFamily(233).family,'MERGED');
 assert.equal(delistingFamily(233).performance_related,false);
 assert.equal(delistingFamily(301).family,'EXCHANGE');
 assert.equal(delistingFamily(450).family,'LIQUIDATION');
 assert.equal(delistingFamily(450).performance_related,true);
 assert.equal(delistingFamily(552).family,'DROPPED');
 assert.equal(delistingFamily(100).family,'STILL_TRADING');
 assert.equal(delistingFamily(null).family,'UNKNOWN');
});

test('a long window is sampled without losing its endpoints',()=>{
 const unique=[close('2020-01-02',10,null)];
 const day=new Date('2020-01-02T00:00:00Z');
 for(let i=1;i<=1200;i++){day.setUTCDate(day.getUTCDate()+1);unique.push(close(day.toISOString().slice(0,10),10+i/100,0.0001));}
 const result=totalReturnSeries(unique,{from:unique[0].date,to:unique.at(-1).date,maxPoints:100});
 assert.equal(result.sampled,true);
 assert.equal(result.series.length,100);
 assert.equal(result.series[0].date,unique[0].date);
 assert.equal(result.series.at(-1).date,unique.at(-1).date);
 assert.equal(result.summary.sessions,unique.length);
});
