PTFKIT_MODEL_INLINE int ptfkit_detail_rosetta(const ptfkit_detail_network *networks,const double *data,unsigned level,unsigned mode,const double *x,size_t count,double *out) {
if(!out)return 0;
for(size_t i=0;i<4;++i)out[i]=NAN;
if(!x || mode>=3)return 0;
switch(level){
case 2:if(count!=1)return 0;break;
default:return 0;}
for(size_t i=0;i<count;++i)if(!isfinite(x[i]))return 0;
if(level>=2 && !(x[0] >= 0.0))return 0;
size_t raw_index=0;switch(level){
case 2:raw_index=0;break;
}
double raw[2];ptfkit_detail_network_predict(&networks[raw_index],data,x,raw);
double physical[2];for(size_t i=0;i<2;++i)physical[i]=raw[i];
for(size_t i=0;i<2;++i)physical[i*1+0]=pow(10.0,raw[i*1+0]);
double log_mean[1],log_std[1];ptfkit_detail_stats(raw,2,1,log_mean,log_std);
double linear_mean[1],linear_std[1];ptfkit_detail_stats(physical,2,1,linear_mean,linear_std);
double geo[1];for(size_t i=0;i<1;++i)geo[i]=log_mean[i];
for(size_t i=0;i<1;++i)geo[i*1+0]=pow(10.0,log_mean[i*1+0]);
const double *mean=NULL;switch(mode){
case 0:mean=linear_mean;break;
case 1:mean=log_mean;break;
case 2:mean=geo;break;
}
const double *std=NULL;switch(mode){
case 0:std=linear_std;break;
case 1:std=log_std;break;
case 2:std=linear_std;break;
}
out[0]=mean[0];
out[1]=std[0];
const double *feed=NULL;switch(mode){
case 0:feed=linear_mean;break;
case 1:feed=geo;break;
case 2:feed=geo;break;
}
double input[]={feed[0]};
if(level>=2 && !(input[0] > 0.0))return 1;
size_t secondary_index=0;switch(level){
case 2:secondary_index=1;break;
}
double secondary[2];ptfkit_detail_network_predict(&networks[secondary_index],data,input,secondary);
double summary_mean[1],summary_std[1];ptfkit_detail_stats(secondary,2,1,summary_mean,summary_std);
out[2]=summary_mean[0];
out[3]=summary_std[0];
return 1;}
