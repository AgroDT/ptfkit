fn mod2(_ptfkit_networks:&[Network],_ptfkit_data:&[f64],_ptfkit_mode:usize,_ptfkit_inputs:&[f64])->Option<[f64;5]>{
if _ptfkit_mode>2 || _ptfkit_inputs.len()!=1 || _ptfkit_inputs.iter().any(|v|!v.is_finite()) {return None;}
let x:f64=_ptfkit_inputs[0];
if !matches!((x).partial_cmp(&(0.0f64)),Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)) {return None;}
if !matches!((x).partial_cmp(&(4.0f64)),Some(std::cmp::Ordering::Less | std::cmp::Ordering::Equal)) {return None;}
let raw=_ptfkit_networks[0].predict(_ptfkit_data,&[x]);
let physical=raw.iter().map(|row|{
let member_value:f64=row[0];
vec![10.0f64 . powf (member_value)]}).collect::<Vec<Vec<f64>>>();
#[allow(dead_code)]
struct Statistics3{
value_mean:f64,
value_std:f64,
}
let (logs_mean,logs_std)=statistics(&raw);
let logs=Statistics3{
value_mean:logs_mean[0],
value_std:logs_std[0],
};
#[allow(dead_code)]
struct Statistics4{
value_mean:f64,
value_std:f64,
}
let (linear_mean,linear_std)=statistics(&physical);
let linear=Statistics4{
value_mean:linear_mean[0],
value_std:linear_std[0],
};
let geometric:f64=10.0f64 . powf (logs . value_mean);
let mean:f64=match _ptfkit_mode{0=>linear . value_mean,1=>logs . value_mean,_=>geometric};
let std:f64=match _ptfkit_mode{0=>linear . value_std,1=>logs . value_std,_=>linear . value_std};
let feed:f64=match _ptfkit_mode{0=>linear . value_mean,1=>geometric,_=>geometric};
let secondary=if matches!((feed).partial_cmp(&(100.0f64)),Some(std::cmp::Ordering::Less)) {_ptfkit_networks[1].predict(_ptfkit_data,&[feed])}else{vec![vec![f64::NAN;1];2]};
#[allow(dead_code)]
struct Statistics10{
value_mean:f64,
value_std:f64,
}
let (summary_mean,summary_std)=statistics(&secondary);
let summary=Statistics10{
value_mean:summary_mean[0],
value_std:summary_std[0],
};
let secondary_mean:f64=summary . value_mean;
let secondary_std:f64=summary . value_std;
let shifted:f64=secondary_mean + 7.0f64;
Some([mean,std,secondary_mean,secondary_std,shifted])
}
