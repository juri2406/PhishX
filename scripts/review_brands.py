"""Check the finite starter registry without overriding any model verdict."""
import argparse
import json
from pathlib import Path
from phishx.skeleton import brands
from phishx import analyze_url


def review(output):
    cases=[]
    for brand, domains in brands().items():
        for domain in domains:
            for url in ['https://'+domain+'/login','https://www.'+domain+'/account']:
                result=analyze_url(url)['brand_match']
                assert result['legitimate_brand_domain'] and not result['impersonation_signal']
                cases.append({'kind':'legitimate-domain','brand':brand,'url':url,'match':result})
        name=brand
        for latin,cyrillic in [('a','а'),('e','е'),('o','о'),('i','і')]:
            if latin in name:
                name=name.replace(latin,cyrillic,1);break
        url='https://'+name+'.example/login'
        result=analyze_url(url)['brand_match']
        assert result['closest_brand']==brand and result['impersonation_signal']
        cases.append({'kind':'synthetic-lookalike','brand':brand,'url':url,'match':result})
        url='https://'+brand+'.attacker.example'
        result=analyze_url(url)
        assert result['features']['brand_in_subdomain']==1 and result['brand_match']['impersonation_signal']
        cases.append({'kind':'synthetic-subdomain','brand':brand,'url':url,'match':result['brand_match']})
        url='https://unrelated.example/'+brand
        assert not analyze_url(url)['brand_match']['impersonation_signal']
        cases.append({'kind':'brand-in-path-only','brand':brand,'url':url,'impersonation_signal':False})
    report={'brands':len(brands()),'domains':sum(map(len,brands().values())), 'checks':cases,
            'scope':'Finite curated starter registry: exact legitimate-domain exclusions and synthetic pattern checks. No universal coverage, live-compromise verification or model-score override.'}
    target=Path(output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{len(cases)} checks passed across {report["brands"]} brands and {report["domains"]} domains')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output')
    a=p.parse_args();review(a.output)
