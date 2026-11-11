use super::engine::{Network,statistics};
pub fn predict(networks:&[Network],data:&[f64],level:usize,mode:usize,x:&[f64])->Option<[f64;4]> {
if mode>=3 {return None;}
match level {
2=>if x.len()!=1 {return None;},
_=>return None,}
if x.iter().any(|v|!v.is_finite()) {return None;}
if level>=2 && !matches!((x[0]).partial_cmp(&(0.0)), Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)) {return None;}
let mut out=[f64::NAN;4];
let raw_index=match level{
2=>0,
_=>unreachable!(),};
let raw=networks[raw_index].predict(data,x);
let mut physical=raw.clone();
for row in &mut physical {row[0]=10.0_f64.powf(row[0]);}
let (log_mean,log_std)=statistics(&raw);
let log_mean=[log_mean];let log_std=[log_std];
let (linear_mean,linear_std)=statistics(&physical);
let linear_mean=[linear_mean];let linear_std=[linear_std];
let mut geo=log_mean.clone();
for row in &mut geo {row[0]=10.0_f64.powf(row[0]);}
let mean=match mode{
0=>&linear_mean,
1=>&log_mean,
2=>&geo,
_=>unreachable!(),};
let std=match mode{
0=>&linear_std,
1=>&log_std,
2=>&linear_std,
_=>unreachable!(),};
out[0]=mean[0][0];
out[1]=std[0][0];
let feed=match mode{
0=>&linear_mean,
1=>&geo,
2=>&geo,
_=>unreachable!(),};
let input=[vec![feed[0][0]]];
if level>=2 && !matches!((input[0][0]).partial_cmp(&(0.0)), Some(std::cmp::Ordering::Greater)) {return Some(out);}
let secondary_index=match level{
2=>1,
_=>unreachable!(),};
let secondary=networks[secondary_index].predict(data,&input[0]);
let (summary_mean,summary_std)=statistics(&secondary);
let summary_mean=[summary_mean];let summary_std=[summary_std];
out[2]=summary_mean[0][0];
out[3]=summary_std[0][0];
Some(out)
}
