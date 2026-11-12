PTFKIT_MODEL_INLINE int ptfkit_detail_dense_mod2(const ptfkit_detail_network *_ptfkit_networks,const double *_ptfkit_data,unsigned _ptfkit_mode,const double *_ptfkit_inputs,size_t _ptfkit_count,double *_ptfkit_out){
if(!_ptfkit_inputs || !_ptfkit_out)return 0;
for(size_t i=0;i<5;++i)_ptfkit_out[i]=NAN;
if(_ptfkit_mode>2 || _ptfkit_count!=1)return 0;
for(size_t i=0;i<_ptfkit_count;++i)if(!isfinite(_ptfkit_inputs[i]))return 0;
const double x=_ptfkit_inputs[0];
if(!(x >= 0.0))return 0;
if(!(x <= 4.0))return 0;
double raw[2];
const double _ptfkit_raw_inputs[]={x};
ptfkit_detail_network_predict(&_ptfkit_networks[0],_ptfkit_data,_ptfkit_raw_inputs,raw);
double physical[2];
for(size_t member=0;member<2;++member){
const double member_value=raw[member*1+0];
physical[member*1+0]=pow(10.0, member_value);
}
struct{
double value_mean;
double value_std;
}logs;
double logs_mean[1],logs_std[1];
ptfkit_detail_stats(raw,2,1,logs_mean,logs_std);
logs.value_mean=logs_mean[0];
logs.value_std=logs_std[0];
struct{
double value_mean;
double value_std;
}linear;
double linear_mean[1],linear_std[1];
ptfkit_detail_stats(physical,2,1,linear_mean,linear_std);
linear.value_mean=linear_mean[0];
linear.value_std=linear_std[0];
const double geometric=pow(10.0, logs.value_mean);
const double mean=_ptfkit_mode==0 ? linear.value_mean : _ptfkit_mode==1 ? logs.value_mean : geometric;
const double std=_ptfkit_mode==0 ? linear.value_std : _ptfkit_mode==1 ? logs.value_std : linear.value_std;
const double feed=_ptfkit_mode==0 ? linear.value_mean : _ptfkit_mode==1 ? geometric : geometric;
double secondary[2];
for(size_t i=0;i<2;++i)secondary[i]=NAN;
if((feed < 100.0)){
const double _ptfkit_secondary_inputs[]={feed};
ptfkit_detail_network_predict(&_ptfkit_networks[1],_ptfkit_data,_ptfkit_secondary_inputs,secondary);
}
struct{
double value_mean;
double value_std;
}summary;
double summary_mean[1],summary_std[1];
ptfkit_detail_stats(secondary,2,1,summary_mean,summary_std);
summary.value_mean=summary_mean[0];
summary.value_std=summary_std[0];
const double secondary_mean=summary.value_mean;
const double secondary_std=summary.value_std;
const double shifted=secondary_mean + 7.0;
_ptfkit_out[0]=mean;
_ptfkit_out[1]=std;
_ptfkit_out[2]=secondary_mean;
_ptfkit_out[3]=secondary_std;
_ptfkit_out[4]=shifted;
return 1;}
