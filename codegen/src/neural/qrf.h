#ifndef PTFKIT_DETAIL_QRF_H
#define PTFKIT_DETAIL_QRF_H
#define PTFKIT_EUPTF2_THS_SHA256 "@QRF_SHA256@"
typedef struct {
    uint32_t left, right, feature;
    double value, sample;
} ptfkit_detail_qrf_node;
/* Owned single forest; fields are private and immutable. */
typedef struct {
    size_t detail_trees, detail_features;
    size_t *detail_offsets;
    ptfkit_detail_qrf_node *detail_nodes;
} ptfkit_euptf2_ths;

PTFKIT_MODEL_INLINE void ptfkit_euptf2_ths_free(ptfkit_euptf2_ths *model) {
    if (model) { free(model->detail_offsets); free(model->detail_nodes); free(model); }
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_detail_qrf_authenticate(
    const unsigned char *bytes, size_t size, const char *sha) {
    if (!bytes || size < 16 || size > PTFKIT_MODEL_MAX_BYTES || !sha || strlen(sha)!=64 ||
        sizeof(double)!=8 || DBL_MANT_DIG!=53 || DBL_MAX_EXP!=1024) return PTFKIT_MODEL_FORMAT;
    unsigned char expected[32], actual[32];
    for (size_t i=0;i<32;++i) {
        int a=ptfkit_detail_unhex(sha[2*i]), b=ptfkit_detail_unhex(sha[2*i+1]);
        if(a<0 || b<0) return PTFKIT_MODEL_FORMAT;
        expected[i]=(unsigned char)(a*16+b);
    }
    ptfkit_detail_sha256(bytes,size,actual);
    return memcmp(expected,actual,32) ? PTFKIT_MODEL_INTEGRITY : PTFKIT_MODEL_OK;
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_detail_qrf_read_forest(
    ptfkit_detail_reader *r, size_t features, ptfkit_euptf2_ths **out) {
    size_t count = (size_t)ptfkit_detail_read(r, 4);
    if (count < 1 || count > 1000) return PTFKIT_MODEL_FORMAT;
    ptfkit_euptf2_ths *model = (ptfkit_euptf2_ths *)calloc(1, sizeof(*model));
    if (!model) return PTFKIT_MODEL_MEMORY;
    model->detail_trees = count;
    model->detail_features = features;
    ptfkit_detail_reader probe=*r;
    size_t total=0, largest=0;
    for(size_t tree=0;tree<count;++tree) {
        size_t n=(size_t)ptfkit_detail_read(&probe,4);
        if(probe.invalid || !n || n>(probe.size-probe.pos)/28) { free(model); return PTFKIT_MODEL_FORMAT; }
        total+=n; if(n>largest) largest=n; probe.pos+=n*28;
    }
    model->detail_offsets = (size_t *)calloc(count+1, sizeof(size_t));
    model->detail_nodes = (ptfkit_detail_qrf_node *)calloc(total, sizeof(ptfkit_detail_qrf_node));
    unsigned char *parents = (unsigned char *)malloc(largest);
    if (!model->detail_offsets || !model->detail_nodes || !parents) {
        free(parents); ptfkit_euptf2_ths_free(model); return PTFKIT_MODEL_MEMORY;
    }
    size_t end = 0;
    for (size_t tree = 0; tree < count && !r->invalid; ++tree) {
        size_t n = (size_t)ptfkit_detail_read(r, 4);
        if (r->invalid || n == 0 || n > (r->size-r->pos)/28) { r->invalid = 1; break; }
        memset(parents, 0, n);
        model->detail_offsets[tree] = end;
        for (size_t i = 0; i < n; ++i) {
            ptfkit_detail_qrf_node *node = &model->detail_nodes[end+i];
            node->left = (uint32_t)ptfkit_detail_read(r, 4);
            node->right = (uint32_t)ptfkit_detail_read(r, 4);
            node->feature = (uint32_t)ptfkit_detail_read(r, 4);
            node->value = ptfkit_detail_read_double(r);
            node->sample = ptfkit_detail_read_double(r);
            if (!node->left && !node->right) {
                if (node->feature != UINT32_MAX) r->invalid = 1;
            } else if (node->left <= i || node->right <= i || node->left >= n ||
                       node->right >= n || node->left == node->right || node->feature >= features || node->sample != 0) {
                r->invalid = 1;
            } else {
                if (parents[node->left] || parents[node->right]) r->invalid = 1;
                parents[node->left] = parents[node->right] = 1;
            }
        }
        for (size_t i = 1; i < n; ++i) if (parents[i] != 1) r->invalid = 1;
        end += n;
    }
    free(parents);
    model->detail_offsets[count] = end;
    if (r->invalid) {
        ptfkit_euptf2_ths_free(model); return PTFKIT_MODEL_FORMAT;
    }
    *out = model;
    return PTFKIT_MODEL_OK;
}

PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_detail_qrf_decode(
    const unsigned char *bytes, size_t size, const char *sha, ptfkit_euptf2_ths **out) {
    if(!out) return PTFKIT_MODEL_INPUT;
    *out=NULL;
    ptfkit_model_status status=ptfkit_detail_qrf_authenticate(bytes,size,sha);
    if(status!=PTFKIT_MODEL_OK) return status;
    if(memcmp(bytes,"PTFKQF01",8)) return PTFKIT_MODEL_FORMAT;
    ptfkit_detail_reader r={bytes,size,8,0};
    if(ptfkit_detail_read(&r,4)!=1) return PTFKIT_MODEL_FORMAT;
    status=ptfkit_detail_qrf_read_forest(&r,4,out);
    if(status==PTFKIT_MODEL_OK && r.pos!=size) {
        ptfkit_euptf2_ths_free(*out); *out=NULL; return PTFKIT_MODEL_FORMAT;
    }
    return status;
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_euptf2_ths_from_bytes(
    const unsigned char *bytes, size_t size, ptfkit_euptf2_ths **out) {
    return ptfkit_detail_qrf_decode(bytes,size,PTFKIT_EUPTF2_THS_SHA256,out);
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_detail_qrf_file(
    const char *path, unsigned char **bytes, size_t *size) {
    if(!path) return PTFKIT_MODEL_INPUT;
    FILE *file=fopen(path,"rb");
    if(!file) return PTFKIT_MODEL_IO;
    if(fseek(file,0,SEEK_END)) { fclose(file); return PTFKIT_MODEL_IO; }
    long length=ftell(file);
    if(length<16 || (unsigned long)length>PTFKIT_MODEL_MAX_BYTES) { fclose(file); return PTFKIT_MODEL_FORMAT; }
    rewind(file);
    *bytes=(unsigned char*)malloc((size_t)length);
    if(!*bytes) { fclose(file); return PTFKIT_MODEL_MEMORY; }
    *size=fread(*bytes,1,(size_t)length,file);
    int extra=fgetc(file), failed=ferror(file);
    fclose(file);
    if(failed || *size!=(size_t)length || extra!=EOF) { free(*bytes); *bytes=NULL; return PTFKIT_MODEL_IO; }
    return PTFKIT_MODEL_OK;
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_euptf2_ths_load(const char *path, ptfkit_euptf2_ths **out) {
    if(!out) return PTFKIT_MODEL_INPUT;
    *out=NULL; unsigned char *bytes=NULL; size_t size=0;
    ptfkit_model_status status=ptfkit_detail_qrf_file(path,&bytes,&size);
    if(status==PTFKIT_MODEL_OK) status=ptfkit_euptf2_ths_from_bytes(bytes,size,out);
    free(bytes); return status;
}
PTFKIT_MODEL_INLINE int ptfkit_detail_qrf_compare(const void *a,const void *b) {
    double x=*(const double*)a,y=*(const double*)b; return (x>y)-(x<y);
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_detail_qrf_statistics(
    const ptfkit_euptf2_ths *model, const double *inputs, size_t nin,
    const double *probabilities, size_t nq, double *mean, double *quantiles) {
    if (!model || !inputs || nin != model->detail_features) return PTFKIT_MODEL_INPUT;
    for (size_t i = 0; i < nin; ++i) if (isnan(inputs[i])) return PTFKIT_MODEL_INPUT;
    double samples[1000], sum = 0;
    for (size_t tree = 0; tree < model->detail_trees; ++tree) {
        const ptfkit_detail_qrf_node *nodes = model->detail_nodes + model->detail_offsets[tree];
        const ptfkit_detail_qrf_node *node = nodes;
        while (node->left) node = &nodes[inputs[node->feature] <= node->value ? node->left : node->right];
        sum += node->value;
        samples[tree] = node->sample;
    }
    qsort(samples, model->detail_trees, sizeof(double), ptfkit_detail_qrf_compare);
    *mean = sum / (double)model->detail_trees;
    for (size_t i = 0; i < nq; ++i) {
        double h = (double)(model->detail_trees-1) * probabilities[i];
        size_t lo = (size_t)floor(h), hi = (size_t)ceil(h);
        double g = h - (double)lo;
        quantiles[i] = samples[lo] == samples[hi] ? samples[lo] : (1-g)*samples[lo]+g*samples[hi];
    }
    return PTFKIT_MODEL_OK;
}

PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_euptf2_ths_predict(
    const ptfkit_euptf2_ths *model, const double inputs[4], double out[4]) {
    if(!out) return PTFKIT_MODEL_INPUT;
    for(size_t i=0;i<4;++i) out[i]=NAN;
    const double probabilities[3]={.05,.5,.95};
    return ptfkit_detail_qrf_statistics(model,inputs,4,probabilities,3,&out[0],out+1);
}
/* Scientific identities and metadata, with no trained arrays. */
typedef struct {
    unsigned id;
    const char *name, *sha256;
    size_t inputs, components, means;
    const char *input_names[9], *output_names[7];
    unsigned transforms[6];
} ptfkit_euptf2_contract;
PTFKIT_MODEL_INLINE const ptfkit_euptf2_contract *ptfkit_euptf2_contracts(size_t *count) {
    static const ptfkit_euptf2_contract models[] = {
@EUPTF2_C_CONTRACTS@
    };
    if(count) *count=sizeof(models)/sizeof(models[0]);
    return models;
}
typedef struct {
    const ptfkit_euptf2_contract *detail_contract;
    ptfkit_euptf2_ths *detail_forests[6];
} ptfkit_euptf2_model;
PTFKIT_MODEL_INLINE void ptfkit_euptf2_free(ptfkit_euptf2_model *model) {
    if(model) { for(size_t i=0;i<6;++i) ptfkit_euptf2_ths_free(model->detail_forests[i]); free(model); }
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_detail_euptf2_parse(
    const ptfkit_euptf2_contract *contract, const unsigned char *bytes, size_t size,
    ptfkit_euptf2_model **out) {
    if(size<20 || memcmp(bytes,"PTFKQF02",8)) return PTFKIT_MODEL_FORMAT;
    ptfkit_detail_reader r={bytes,size,8,0};
    if(ptfkit_detail_read(&r,4)!=contract->id || ptfkit_detail_read(&r,4)!=contract->inputs ||
       ptfkit_detail_read(&r,4)!=contract->components) return PTFKIT_MODEL_FORMAT;
    ptfkit_euptf2_model *model=(ptfkit_euptf2_model*)calloc(1,sizeof(*model));
    if(!model) return PTFKIT_MODEL_MEMORY;
    model->detail_contract=contract;
    ptfkit_model_status status=PTFKIT_MODEL_OK;
    for(size_t i=0;i<contract->components;++i) {
        if(ptfkit_detail_read(&r,4)!=contract->transforms[i]) { status=PTFKIT_MODEL_FORMAT; break; }
        status=ptfkit_detail_qrf_read_forest(&r,contract->inputs,&model->detail_forests[i]);
        if(status!=PTFKIT_MODEL_OK) break;
    }
    if(status==PTFKIT_MODEL_OK && (r.invalid || r.pos!=size)) status=PTFKIT_MODEL_FORMAT;
    if(status!=PTFKIT_MODEL_OK) { ptfkit_euptf2_free(model); return status; }
    *out=model; return PTFKIT_MODEL_OK;
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_euptf2_from_bytes(
    const char *name, const unsigned char *bytes, size_t size, ptfkit_euptf2_model **out) {
    if(!out || !name) return PTFKIT_MODEL_INPUT;
    *out=NULL;
    size_t count; const ptfkit_euptf2_contract *all=ptfkit_euptf2_contracts(&count), *contract=NULL;
    for(size_t i=0;i<count;++i) if(strcmp(name,all[i].name)==0) { contract=all+i; break; }
    if(!contract) return PTFKIT_MODEL_INPUT;
    ptfkit_model_status status=ptfkit_detail_qrf_authenticate(bytes,size,contract->sha256);
    if(status!=PTFKIT_MODEL_OK) return status;
    return ptfkit_detail_euptf2_parse(contract,bytes,size,out);
}
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_euptf2_load(
    const char *name,const char *path,ptfkit_euptf2_model **out) {
    if(!out) return PTFKIT_MODEL_INPUT;
    *out=NULL; unsigned char *bytes=NULL; size_t size=0;
    ptfkit_model_status status=ptfkit_detail_qrf_file(path,&bytes,&size);
    if(status==PTFKIT_MODEL_OK) status=ptfkit_euptf2_from_bytes(name,bytes,size,out);
    free(bytes); return status;
}
PTFKIT_MODEL_INLINE double ptfkit_detail_euptf2_transform(double value,unsigned transform) {
    switch(transform) { case 0:return value; case 1:return pow(10,value); case 2:return pow(10,value)-1; default:return pow(10,value)+1; }
}
/* Quantiles are parameter-major. NULL probabilities selects the five defaults,
   with nq=5. Counts must match the contract and supplied storage exactly. */
PTFKIT_MODEL_INLINE ptfkit_model_status ptfkit_euptf2_predict(
    const ptfkit_euptf2_model *model, const double *inputs, size_t nin,
    const double *probabilities, size_t nq, double *means, size_t nm,
    double *quantiles, size_t nv) {
    if(!means || !quantiles || nm>7 || nv>384) return PTFKIT_MODEL_INPUT;
    for(size_t i=0;i<nm;++i) means[i]=NAN;
    for(size_t i=0;i<nv;++i) quantiles[i]=NAN;
    if(!model || nq<1 || nq>64) return PTFKIT_MODEL_INPUT;
    const ptfkit_euptf2_contract *c=model->detail_contract;
    if(nin!=c->inputs || nm!=c->means || nv!=c->components*nq) return PTFKIT_MODEL_INPUT;
    const double defaults[5]={.05,.25,.5,.75,.95};
    if(!probabilities) { if(nq!=5) return PTFKIT_MODEL_INPUT; probabilities=defaults; }
    for(size_t i=0;i<nq;++i) if(!(probabilities[i]>0 && probabilities[i]<1)) return PTFKIT_MODEL_INPUT;
    for(size_t i=0;i<c->components;++i) {
        ptfkit_model_status status=ptfkit_detail_qrf_statistics(model->detail_forests[i],inputs,nin,probabilities,nq,means+i,quantiles+i*nq);
        if(status!=PTFKIT_MODEL_OK) return status;
        means[i]=ptfkit_detail_euptf2_transform(means[i],c->transforms[i]);
        for(size_t j=0;j<nq;++j) quantiles[i*nq+j]=ptfkit_detail_euptf2_transform(quantiles[i*nq+j],c->transforms[i]);
    }
    if(c->means>c->components) means[c->components]=1-1/means[3];
    return PTFKIT_MODEL_OK;
}
#endif
