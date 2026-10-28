import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const runtime = 'C:/Users/Payas/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill = 'C:/Users/Payas/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11127/skills/presentations';
process.env.RUNTIME_NODE_MODULES = path.join(runtime,'node/node_modules');
const {Presentation, PresentationFile} = await import(pathToFileURL(path.join(process.env.RUNTIME_NODE_MODULES,'@oai/artifact-tool/dist/artifact_tool.mjs')));
const {finalizePresentation, applyPresentationChartFont} = await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const m = JSON.parse(await fs.readFile(path.join(root,'artifacts/metrics.json'),'utf8'));
const student = JSON.parse(await fs.readFile(path.join(root,'docs/student.json'),'utf8'));
const csv = (await fs.readFile(path.join(root,'artifacts/comparison.csv'),'utf8')).trim().split(/\r?\n/).map(x=>x.split(','));
const models = csv.slice(1).map(r=>Object.fromEntries(csv[0].map((h,i)=>[h,i?Number(r[i]):r[i]])));
const build = path.join(root,'.build/slides');
await fs.mkdir(build,{recursive:true});
await fs.mkdir(path.join(root,'deliverables'),{recursive:true});
const ppt = Presentation.create({slideSize:{width:1280,height:720}});
const ink='#132F46', teal='#087E8B', grey='#586B7B', paper='#F8FAFC', font='Arial';
const pct = x=>(x*100).toFixed(2)+'%';
const source='Source: artifacts/metrics.json and artifacts/comparison.csv, local experiment, 22 October 2026.';
function txt(slide,text,x,y,w,h,size=28,color=ink,bold=false){
  const sh=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=text; sh.text.style={fontFamily:font,fontSize:size,color,bold}; return sh;
}
function slide(title, notes='', dark=false){
  const sl=ppt.slides.add(); sl.background.fill=dark?ink:paper;
  txt(sl,'PDEU   /   MACHINE LEARNING LABORATORY',64,28,1050,25,16,dark?'#97D8DC':teal,true);
  txt(sl,title,64,80,1152,96,42,dark?'#FFFFFF':ink,true);
  txt(sl,'Payas Vaishnav   •   23BCP430',64,674,900,22,15,dark?'#B7CEDB':grey);
  txt(sl,String(ppt.slides.items.length).padStart(2,'0'),1160,674,60,22,15,dark?'#B7CEDB':grey);
  sl.speakerNotes.text=notes; return sl;
}
function body(sl,text,y=200,size=29,w=1120){txt(sl,text,72,y,w,425,size,ink);}
function table(sl, headers, values, opts={}){
  const {x=72,y=196,w=1136,h=405,widths=null,size=23}=opts;
  const t=sl.tables.add({rows:values.length+1,columns:headers.length,left:x,top:y,width:w,height:h,values:[headers,...values],...(widths?{columnWidths:widths}:{})});
  t.borders.assign({fill:'#D9E2EA',width:1,style:'solid'});
  t.cells.block({row:0,column:0,rowCount:values.length+1,columnCount:headers.length}).assign({textStyle:{fontFamily:font,fontSize:size,color:ink},margins:{left:12,right:12,top:6,bottom:6},anchor:'center'});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:headers.length}).assign({fill:ink,textStyle:{fontFamily:font,fontSize:size,color:'#FFFFFF',bold:true}});
  for(let r=1;r<=values.length;r++)t.cells.block({row:r,column:0,rowCount:1,columnCount:headers.length}).assign({fill:r%2?'#EAF2F5':'#FFFFFF'});
  return t;
}
function chart(sl,categories,values,opts={}){
  const ch=sl.charts.add('bar',{position:{left:64,top:188,width:1140,height:420},categories,
    series:[{name:opts.name||'Macro F1',values,fill:teal}],hasLegend:false,
    barOptions:{direction:opts.horizontal?'bar':'column',grouping:'clustered',gapWidth:60},
    xAxis:{textStyle:{typeface:font,fontSize:opts.labelSize||20,fill:grey},line:{fill:'#CBD5E1',width:1}},
    yAxis:{min:0,...(opts.max?{max:opts.max}:{}),numberFormatCode:opts.format||'0.00',textStyle:{typeface:font,fontSize:18,fill:grey},majorGridlines:{fill:'#E2E8F0',width:1}},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:opts.format||'0.0000',textStyle:{typeface:font,fontSize:19,fill:ink}}});
  applyPresentationChartFont(ch,{fontFamily:font});return ch;
}

let sl=slide('Network Intrusion Detection\nUsing Machine Learning', 'Introduce the project as offline classification of recorded network flows. Explain that the project includes an experiment pipeline and dashboard. It uses sampled CICIDS2017 data and credits Western OC2 Lab. Do not describe this as a deployed firewall.',true);
txt(sl,'Comparative evaluation on sampled CICIDS2017 traffic',72,306,1110,70,30,'#B9DCE5');
txt(sl,student.name+'   /   '+student.roll,72,445,1100,42,29,'#FFFFFF',true);
txt(sl,'CSE, PDEU   •   Semester 7\nFaculty guide: '+student.guide,72,505,1100,92,24,'#B7CEDB');

sl=slide('The traffic classification problem','Each input row summarizes one flow. A flow differs from a packet. The target label is known during training and predicted during inference. The implementation accepts recorded measurements and does not capture packets or automatically block traffic. Dataset documentation: https://www.unb.ca/cic/datasets/ids-2017.html');
txt(sl,'INPUT',72,205,220,35,22,teal,true);
txt(sl,'Flow duration, packet counts, lengths, timing and flags',72,253,1090,80,36);
txt(sl,'OUTPUT',72,365,220,35,22,teal,true);
txt(sl,'BENIGN or a known attack category',72,413,1090,65,36);
txt(sl,'A local CSV analysis tool for investigating recorded traffic',72,553,1090,60,26,grey);

sl=slide('The dataset contains strongly unequal classes',source+' CICIDS2017 sample provided by Western OC2 Lab: https://github.com/Western-OC2-Lab/Intrusion-Detection-System-Using-Machine-Learning. The full original dataset has more traffic and collection metadata. These are counts after deduplication. Infiltration has only 36 distinct examples.');
table(sl,['Traffic category','Distinct flows'],Object.entries(m.class_counts).map(([k,v])=>[k,v.toLocaleString()]),{w:700,widths:[440,260],h:418});
txt(sl,m.rows.toLocaleString(),840,220,360,75,62,teal,true);
txt(sl,'distinct flows',840,300,330,48,27);
txt(sl,'77 features\n7 labels\n36 Infiltration flows',840,390,350,145,29);

sl=slide('Data preparation protects the comparison','Cleaning is deterministic and occurs before model fitting. Exact duplicate feature rows are removed before splitting. Missing-value imputation fits inside the model pipeline. Exact deduplication cannot guarantee independent flows. If features repeat with conflicting labels the first row is retained.');
body(sl,'01   Trim column names and traffic labels\n\n02   Convert measurements and mark infinities as missing\n\n03   Remove 12,610 duplicate feature rows\n\n04   Split distinct flows with stratification and seed 42\n\n05   Fit median imputation within each fitting pipeline',190,29);

sl=slide('Training validation and test partitions','The split is 60/20/20. Training supports fitting and three-fold CV. Validation macro F1 selects a configuration. Refit the winner on training plus validation before evaluation. The same fixed test partition appeared in the initial prototype, so the final result is an internal benchmark, not independent external validation. '+source);
chart(sl,['Training','Validation','Test'],[m.split.train,m.split.validation,m.split.test],{name:'Flows',format:'#,##0',max:30000,labelSize:25});
txt(sl,'Fit and tune',182,618,230,35,23,grey);
txt(sl,'Select model',545,618,230,35,23,grey);
txt(sl,'Report scores',908,618,230,35,23,grey);

sl=slide('Eight configurations test different choices','A majority classifier establishes the baseline. Decision Tree, Random Forest and Extra Trees are standard tree methods. Histogram Gradient Boosting is scikit-learn boosting and is not XGBoost. Stacking combines a tree and Extra Trees through logistic regression using out-of-fold base predictions. Source: train.py and https://scikit-learn.org/stable/modules/ensemble.html');
table(sl,['Configuration','Purpose'],[
['Majority baseline','Check performance without useful learning'],['Decision Tree','Establish an interpretable tree comparator'],['Tuned Decision Tree','Test a bounded hyperparameter search'],['Random Forest','Average 120 randomized trees'],['Extra Trees','Test stronger split randomness'],['Histogram Gradient Boosting','Learn sequentially with boosted trees'],['Top 20 features Tree','Measure the cost of reducing inputs'],['Stacking ensemble','Combine tree predictions with a meta-model']
],{widths:[430,706],h:432,size:23});

sl=slide('Tuning and feature selection are experiments','Tree search samples 12 settings from 40 possible combinations, with 3 folds per candidate on training data only. Maximum depth: 8,12,20,30 or unlimited. Minimum leaf size: 1,2,4,8. Criterion: gini or entropy. The 20-feature ANOVA selector fits inside each pipeline. Constant feature warnings appear in the log. '+source);
txt(sl,'12',72,205,280,88,72,teal,true);txt(sl,'tree configurations',72,299,480,52,29);
txt(sl,'20 / 77',710,205,460,88,72,teal,true);txt(sl,'selected feature measurements',710,299,480,80,29);
txt(sl,'Three training folds score each tree candidate.\nValidation results decide whether the added complexity helps.',72,444,1100,120,30);
txt(sl,'Search winner: unlimited depth, leaf size 1, Gini criterion',72,588,1130,42,24,grey);

sl=slide('Boosting achieves the highest validation macro F1','Validation macro F1 chooses the winner. The boosting margin over the original tree is small, so do not claim a statistically established improvement. More complex stacking did not help with this particular configuration. '+source);
chart(sl,models.map(r=>r.model.replace('Histogram Gradient Boosting','Histogram boosting').replace('Top 20 features Tree','Top 20 features')),models.map(r=>r.validation_macro_f1),{horizontal:true,max:1.08,labelSize:19});
txt(sl,'Macro F1 gives each traffic category equal weight',72,620,1110,32,24,grey);

sl=slide('Cross validation shows variation across folds','These scores use 3 folds of the training partition. Standard deviations are fold dispersion, not confidence intervals. The tuned tree score reuses the search folds and is an optimistic search diagnostic rather than nested CV. Random Forest leads the original tree in training CV but validation macro F1 chooses boosting. '+source);
table(sl,['Configuration','CV mean macro F1','Fold standard deviation'],models.map(r=>[r.model,r.cv_macro_f1_mean.toFixed(4),r.cv_macro_f1_std.toFixed(4)]),{widths:[530,303,303],h:425,size:22});
txt(sl,'Tuned-tree CV reuses search folds. Selection uses validation macro F1.',72,633,1136,28,20,grey);

sl=slide('The selected model reaches 99.61 percent test accuracy','The selected configuration is Histogram Gradient Boosting, refitted on training plus validation. Report both accuracy and macro F1. The percentile bootstrap is stratified by label and uses 300 resamples. Its interval does not include model selection, correlated traffic or dataset shift. '+source,true);
txt(sl,pct(m.test_accuracy),72,215,530,112,88,'#FFFFFF',true);
txt(sl,'Test accuracy',72,341,530,50,30,'#B7CEDB');
txt(sl,m.test_macro_f1.toFixed(4),710,215,490,112,88,'#97D8DC',true);
txt(sl,'Test macro F1',710,341,490,50,30,'#B7CEDB');
txt(sl,'Accuracy interval  '+pct(m.accuracy_ci95[0])+' to '+pct(m.accuracy_ci95[1])+'\nMacro F1 interval  '+m.macro_f1_ci95.map(x=>x.toFixed(4)).join(' to '),72,477,1120,95,29,'#FFFFFF');
txt(sl,'95% stratified bootstrap intervals on 8,811 test flows',72,599,1120,36,22,'#B7CEDB');

sl=slide('Per class metrics reveal uneven evidence','Read precision, recall and support together. Infiltration is scarce, with just 7 test examples, so its perfect score is weak evidence. Bot has the lowest F1 in this run. Scores apply to this internal random split. '+source);
table(sl,['Label','Precision','Recall','F1','Support'],m.labels.map(k=>{const r=m.classification_report[k];return[k,r.precision.toFixed(4),r.recall.toFixed(4),r['f1-score'].toFixed(4),String(r.support)];}),{widths:[300,210,210,210,206],h:412,size:24});
txt(sl,'Infiltration has only 7 test examples. Its perfect score needs caution.',72,628,1130,35,23,grey);

sl=slide('The confusion matrix identifies specific errors','Rows show actual labels and columns show predicted labels. Abbreviated labels keep the native table readable. Brute means BruteForce, Infil means Infiltration, Port means PortScan, Web means WebAttack. The table contains the exact test confusion counts. '+source);
const short=['Benign','Bot','Brute','DoS','Infil','Port','Web'];
table(sl,['Actual / Pred.',...short],m.confusion_matrix.map((r,i)=>[short[i],...r.map(String)]),{widths:[205,133,133,133,133,133,133,133],h:415,size:23});
txt(sl,'Rows = actual traffic     Columns = predicted traffic',72,629,1100,33,24,grey);

const b=m.binary_confusion_matrix;
sl=slide('Nine attack flows are predicted as benign','Collapsing the multiclass result to normal versus attack makes the operating errors clear. There are 22 false alarms among 4338 benign flows, and 9 missed attacks among 4473 attack flows. Other mistakes confuse attack classes. There is no separate alert-threshold optimization or calibrated confidence model. '+source);
table(sl,['Actual traffic','Predicted normal','Predicted attack'],[['Normal',String(b[0][0]),String(b[0][1])],['Attack',String(b[1][0]),String(b[1][1])]],{h:205,widths:[400,368,368],size:29});
txt(sl,pct(m.binary_attack_recall),72,456,530,83,60,teal,true);txt(sl,'Attack detection recall',72,545,530,60,28);
txt(sl,pct(m.binary_false_positive_rate),710,456,490,83,60,ink,true);txt(sl,'Benign false alarm rate',710,545,490,60,28);

sl=slide('The dashboard makes the experiment demonstrable','Run launch.ps1 or the Streamlit command in the README. Model results displays metrics. Detect attacks classifies the supplied 25 held-out demo rows or a compatible uploaded CSV. Experiments shows the bounded search, intervals and error groups. Download predictions to inspect the labels. The saved pipeline contains imputation plus the selected classifier. Source: app.py, ids.py and verify.py.');
body(sl,'Model results\nValidation comparison, test metrics and confusion matrix\n\nDetect attacks\nUpload compatible CSVs and download predicted categories\n\nExperiments\nInspect tree search settings, uncertainty and error groups',195,30);

sl=slide('The experiment can be reproduced locally','The project provides the data hash, seed, pinned environment and partition identifiers. Re-running training rebuilds the fitted model and metric files; runtime measurements may vary. verify.py checks schema rejection and the actual Streamlit prediction interaction. Source: README.md, train.py and verify.py.');
txt(sl,'1   Run training',72,203,520,45,32,teal,true);txt(sl,'.venv\\Scripts\\python.exe train.py',72,266,1110,48,29);
txt(sl,'2   Verify and inspect',72,358,1100,45,32,teal,true);txt(sl,'verify.py   +   IDS_Experiment.ipynb',72,421,1110,48,29);
txt(sl,'3   Start the demo',72,513,1100,45,32,teal,true);txt(sl,'.venv\\Scripts\\python.exe -m streamlit run app.py',72,576,1130,48,27);

sl=slide('Conclusions and evaluation limits','The final conclusion is limited to this sample benchmark. Boosting ranks first on validation macro F1 but its margin over a simple tree is narrow. Stacking, tuning and a smaller feature set did not automatically improve performance. Next evaluate by capture day or session from full source data. The current sample lacks the metadata needed for an honest chronological test. '+source);
txt(sl,'Measured contribution',72,202,1100,45,30,teal,true);
txt(sl,'Eight configurations, reproducible artifacts and a working prediction tool',72,261,1110,100,35);
txt(sl,'Limits',72,398,1100,45,30,teal,true);
txt(sl,'Historical sample, scarce classes and a reused internal test split\nLive capture and unknown-attack detection remain future work',72,457,1110,135,30);

sl=slide('References','The project uses the sample provided by Western OC2 Lab. Original copyright and license are retained under reference/LICENSE. Cite the source research and data. The methods rely on scikit-learn documentation. No external decorative imagery is used.');
body(sl,'Yang et al.  Tree-Based Intelligent Intrusion Detection System in Internet of Vehicles\nIEEE GLOBECOM 2019  •  DOI 10.1109/GLOBECOM38437.2019.9013892\n\nWestern OC2 Lab  •  IDS-ML repository and sampled CSV\ngithub.com/Western-OC2-Lab/Intrusion-Detection-System-Using-Machine-Learning\n\nCanadian Institute for Cybersecurity  •  CICIDS2017\nunb.ca/cic/datasets/ids-2017.html\n\nscikit-learn documentation  •  Ensemble methods and cross-validation\nscikit-learn.org/stable/modules/',194,24);

for(const [i,s] of ppt.slides.items.entries()){
  const png=await ppt.export({slide:s,format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const draft=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(ppt)).save(draft);
const final=path.join(root,'deliverables/IDS_Project_Presentation.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:draft,finalPath:final,
  pythonExecutable:path.join(runtime,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[3,6,9,11,12,13].flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:17,requiredNativeTableOwnerSlides:[3,6,9,11,12,13],requiredNativeChartOwnerSlides:[5,8],
  materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',
  fontPolicy:{basis:'design',families:[font,'Aptos']},verifyArtifactToolImport:true,
  receiptPath:path.join(build,'validation.json')});
console.log(JSON.stringify(result));
