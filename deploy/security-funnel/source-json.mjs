// Bound service responses before parsing. Shared by source-backed query adapters.
export async function boundedSourceJson(response,max=65536){
 if(!response.body)throw Error('DATA_UNAVAILABLE');
 const reader=response.body.getReader(),chunks=[];let bytes=0;
 for(;;){const {done,value}=await reader.read();if(done)break;bytes+=value.length;if(bytes>max){await reader.cancel();throw Error('SOURCE_RESPONSE_TOO_LARGE');}chunks.push(value);}
 const raw=new Uint8Array(bytes);let offset=0;for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.length;}
 return JSON.parse(new TextDecoder().decode(raw));
}
