#include <sstream>

#include "global.hpp"
#include "cnf.hpp"

using namespace std;

Cnf::Cnf(set<int> pes, set<int> mems, vector<tuple<set<int>, set<int>, int> > coms, int ninputs, set<int> output_ids, vector<vector<set<int> > > operands) :ninputs(ninputs), pes(pes), mems(mems), coms(coms), output_ids(output_ids), operands(operands)
{
  nnodes = pes.size() + mems.size();
  ndata = operands.size();
  ncoms = coms.size();
  incoms.resize(nnodes);
  outcoms.resize(nnodes);
  for(int i = 0; i < ncoms; i++) {
    for(int sender : get<0>(coms[i])) {
      outcoms[sender].insert(i);
    }
    for(int recipient : get<1>(coms[i])) {
      incoms[recipient].insert(i);
    }
  }
  assignments[0].resize(ndata);
  for(int i = 0; i < ninputs; i++) {
    assignments[0][i] = 1;
  }
}

void Cnf::write_clause(int &nclauses, vector<int> &vLits) {
  if(nilp) {
    int c = 1;
    for(int lit : vLits) {
      if(lit < 0) {
	f << "-";
	c--;
      }
      f << "x" << abs(lit) << " + ";
    }
    f.seekp(-2, ios::cur);
    f << ">= " << c << endl;
    return;
  }

  // Store clause in all_clauses instead of Glucose solver
  all_clauses.push_back(vLits);
  
  // Write to file if needed
  for(int lit : vLits) {
    f << lit << " ";
  }
  f << 0 << endl;
  nclauses++;
}

void Cnf::amo_naive(int &nclauses, vector<int> &vLits) {
  vector<int> vLits2;
  foreach_comb(vLits.size(), 2, [&](int *indices) {
				  vLits2.clear();
				  vLits2.push_back(-vLits[indices[0]]);
				  vLits2.push_back(-vLits[indices[1]]);
				  write_clause(nclauses, vLits2);
				});
}



void Cnf::amo_bimander(int &nvars, int &nclauses, vector<int> &vLits, int nbim) {
  vector<int> vLits2;
  int m = vLits.size() / nbim + vLits.size() % nbim;
  int nb = integer_log2(m);
  for(int i = 0; i < m; i++) {
    vLits2.clear();
    for(int j = 0; j < nbim && i*nbim + j < (int)vLits.size(); j++) {
      vLits2.push_back(vLits[i*nbim + j]);
    }
    if(vLits2.size() > 1) {
      amo_naive(nclauses, vLits2);
    }
    for(int k = 0; k < nb; k++) {
      int b = 1 << k;
      if(i & b) {
	for(int j = 0; j < nbim && i*nbim + j < (int)vLits.size(); j++) {
	  vLits2.clear();
	  vLits2.push_back(-vLits[i*nbim + j]);
	  vLits2.push_back(nvars + k + 1);
	  write_clause(nclauses, vLits2);
	}
      }
      else {
	for(int j = 0; j < nbim && i*nbim + j < (int)vLits.size(); j++) {
	  vLits2.clear();
	  vLits2.push_back(-vLits[i*nbim + j]);
	  vLits2.push_back(-(nvars + k + 1));
	  write_clause(nclauses, vLits2);
	}
      }
    }
  }
  nvars += nb;
}

void Cnf::amo_commander(int &nvars, int &nclauses, vector<int> vLits) {
  vector<int> vLits2;
  while(vLits.size() > 1) {
    int k = 0;
    for(int j = 0; j < (int)vLits.size()/2; j++) {
      nvars++;
      vLits2.clear();
      vLits2.push_back(-vLits[2*j]);
      vLits2.push_back(-vLits[2*j+1]);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(-nvars);
      vLits2.push_back(vLits[2*j]);
      vLits2.push_back(vLits[2*j+1]);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(nvars);
      vLits2.push_back(-vLits[2*j]);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(nvars);
      vLits2.push_back(-vLits[2*j+1]);
      write_clause(nclauses, vLits2);      
      vLits[k++] = nvars;
    }
    if(vLits.size()%2) {
      vLits[k++] = vLits.back();
    }
    vLits.resize(k);
  }
}

void Cnf::cardinality_amo(int &nvars, int &nclauses, vector<int> &vLits) {
  if(vLits.size() <= 1) {
    return;
  }
  if(nilp) {
    int c = 1;
    for(int lit : vLits) {
      if(lit < 0) {
	f << "-";
	c--;
      }
      f << "x" << abs(lit) << " + ";
    }
    f.seekp(-2, ios::cur);
    f << "<= " << c << endl;
    return;
  }
  switch(nencode) {
  case 0:
    amo_naive(nclauses, vLits);
    break;
  case 1:
    amo_commander(nvars, nclauses, vLits);
    break;
  case 2:
    amo_bimander(nvars, nclauses, vLits, 1); // binary
    break;
  case 3:
    amo_bimander(nvars, nclauses, vLits, 2);
    break;
  case 4:
    amo_bimander(nvars, nclauses, vLits, integer_root(vLits.size()));
    break;
  default:
    show_error("the type of encoding is invalid");
  }
}

void Cnf::cardinality_amk(int &nvars, int &nclauses, vector<int> &vLits, int k) {
  if((int)vLits.size() <= k) {
    return;
  }
  if(nilp) {
    int c = k;
    for(int lit : vLits) {
      if(lit < 0) {
	f << "-";
	c--;
      }
      f << "x" << abs(lit) << " + ";
    }
    f.seekp(-2, ios::cur);
    f << "<= " << c << endl;
    return;
  }
  vector<int> vCounts;
  vector<int> vLits2;
  // first level
  vCounts.push_back(vLits[0]);
  nvars++;
  vLits2.clear();
  vLits2.push_back(-nvars);
  write_clause(nclauses, vLits2);
  for(int i = 1; i < k; i++) {
    vCounts.push_back(nvars);
  }
  // subsequent levels
  for(int j = 1; j < (int)vLits.size(); j++) {
    int x = vLits[j];
    // prohibit overflow (sum>k)
    vLits2.clear();
    vLits2.push_back(-vCounts[k-1]);
    vLits2.push_back(-x);
    write_clause(nclauses, vLits2);
    if(j == (int)vLits.size()-1) {
      break;
    }
    for(int i = k-1; i > 0; i--) {
      // compute AND of x and i-1 of previous level
      nvars++;
      int a = nvars;
      vLits2.clear();
      vLits2.push_back(-a);
      vLits2.push_back(x);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(-a);
      vLits2.push_back(vCounts[i-1]);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(a);
      vLits2.push_back(-x);
      vLits2.push_back(-vCounts[i-1]);
      write_clause(nclauses, vLits2);
      // compute OR of it and i of previous level
      nvars++;
      vLits2.clear();
      vLits2.push_back(-a);
      vLits2.push_back(nvars);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(-vCounts[i]);
      vLits2.push_back(nvars);
      write_clause(nclauses, vLits2);
      vLits2.clear();
      vLits2.push_back(-nvars);
      vLits2.push_back(a);
      vLits2.push_back(vCounts[i]);
      write_clause(nclauses, vLits2);
      // keep it at l of this level
      vCounts[i] = nvars;
    }
    // compute OR of x and 0 of previous level
    nvars++;
    vLits2.clear();
    vLits2.push_back(-x);
    vLits2.push_back(nvars);
    write_clause(nclauses, vLits2);
    vLits2.clear();
    vLits2.push_back(-vCounts[0]);
    vLits2.push_back(nvars);
    write_clause(nclauses, vLits2);
    vLits2.clear();
    vLits2.push_back(-nvars);
    vLits2.push_back(x);
    vLits2.push_back(vCounts[0]);
    write_clause(nclauses, vLits2);
    // keep it at 0 of this level
    vCounts[0] = nvars;
  }
}

void Cnf::support_port() {
  for(int i = 0; i < ncoms; i++) {
    auto com = coms[i];
    set<int> s0, s1;
    if(get<0>(com).size() > 1) {
      for(int j : get<0>(com)) {
	if(nports.count(j) && nports[j].second) {
	  outcoms[j].erase(i);
	  set<int> senders = {j};
	  set<int> recipients;
	  coms.push_back(make_tuple(senders, recipients, 0));
	  outcoms[j].insert(ncoms);
	  bypass[i].insert(ncoms);
	  ncoms++;
	}
	else {
	  s0.insert(j);
	}
      }
    }
    else {
      s0 = get<0>(com);
    }
    if(get<1>(com).size() > 1) {
      for(int j : get<1>(com)) {
	if(nports.count(j) && nports[j].first) {
	  incoms[j].erase(i);
	  set<int> senders;
	  set<int> recipients = {j};
	  coms.push_back(make_tuple(senders, recipients, 0));
	  incoms[j].insert(ncoms);
	  bypass[ncoms].insert(i);
	  ncoms++;
	}
	else {
	  s1.insert(j);
	}
      }
    }
    else {
      s1 = get<1>(com);
    }
    if(get<0>(com).size() != s0.size() || get<1>(com).size() != s1.size()) {
      coms[i] = make_tuple(s0, s1, get<2>(com));
    }
  }
  /*
  cout << "com :" << endl;
  for(auto h : coms) {
    for(int j : get<0>(h)) {
      cout << j << " ";
    }
    cout << "-> ";
    for(int j : get<1>(h)) {
      cout << j << " ";
    }
    if(get<2>(h) > 0) {
      cout << ": " << get<2>(h);
    }
    cout << endl;
  }
  cout << "bypass :" << endl;
  for(auto h : bypass) {
    for(int j : h.second) {
      cout << j << " ";
    }
    cout << "-> ";
    cout << h.first;
    cout << endl;
  }
  */
}

void Cnf::gen_cnf(int ncycles, int nregs, int nprocs, int fextmem, int ncontexts, string filename) {
  ncycles_ = ncycles;
  
  int nvars = ncycles * nnodes * ndata;
  yhead = nvars;
  nvars += ncycles * ncoms * ndata;
  zhead = nvars;
  nvars += ncycles * nnodes * ndata;
  phead = nvars;
  nvars += ncycles * nnodes * nexs;
  qhead = nvars;
  nvars += nsels;
  int nclauses = 0;
  
  // Clear previous clauses
  all_clauses.clear();
  
  if(!nilp) {
    f.setstate(ios_base::badbit);
  }
  else {
    f.open(filename);
  }

  vector<int> vLits;

  if(nilp) {
    f << "minimize" << endl;
    f << "subject to" << endl;
  }
  
  // init condition
  f << (nilp? "\\": "c") << " init condition" << endl;
  for(int j = 0; j < nnodes; j++) {
    for(int i = 0; i < ndata; i++) {
      vLits.clear();
      if(assignments.count(j) && assignments[j][i]) {
	if(assignments[j][i] < 0) {
	  continue;
	}
	vLits.push_back(j*ndata + i + 1);
      }
      else {
	vLits.push_back(-(j*ndata + i + 1));
      }
      write_clause(nclauses, vLits);
    }
  }

  // final condition
  f << (nilp? "\\": "c") << " final condition" << endl;
  for(int i : output_ids) {
    vLits.clear();
    vLits.push_back((ncycles-1)*nnodes*ndata + i + 1);
    write_clause(nclauses, vLits);
  }

  // conditions for node
  f << (nilp? "\\": "c") << " conditions for node" << endl;
  for(int k = 1; k < ncycles; k++) {
    for(int j = 0; j < nnodes; j++) {
      for(int i = 0; i < ndata; i++) {
	vLits.clear();
	vLits.push_back(-(k*nnodes*ndata + j*ndata + i + 1));
	if(tempnodes.empty() || !tempnodes[j]) {
	  vLits.push_back((k-1)*nnodes*ndata + j*ndata + i + 1);
	}
	for(int h : incoms[j]) {
	  vLits.push_back(yhead + k*ncoms*ndata + h*ndata + i + 1);
	}
	vLits.push_back(zhead + k*nnodes*ndata + j*ndata + i + 1);
	write_clause(nclauses, vLits);
      }
    }
  }

  // conditions for communication
  f << (nilp? "\\": "c") << " conditions for communication" << endl;
  for(int k = 1; k < ncycles; k++) {
    for(int h = 0; h < ncoms; h++) {
      for(int i = 0; i < ndata; i++) {
	vLits.clear();
	vLits.push_back(-(yhead + k*ncoms*ndata + h*ndata + i + 1));
	for(int j : get<0>(coms[h])) {
	  vLits.push_back((k-1)*nnodes*ndata + j*ndata + i + 1);
	}
	if(bypass.count(h)) {
	  for(int h2 : bypass[h]) {
	    vLits.push_back(yhead + k*ncoms*ndata + h2*ndata + i + 1);
	  }
	}
	write_clause(nclauses, vLits);
      }
    }
  }

  // conditions for operation
  f << (nilp? "\\": "c") << " conditions for operation" << endl;
  for(int k = 1; k < ncycles; k++) {
    for(int j : pes) {
      for(int i = 0; i < ndata; i++) {
	if(fmulti) {
	  int nvars_ = nvars;
	  for(int si = 0; si < (int)operands[i].size(); si++) {
	    auto &s = operands[i][si];
	    nvars++;
	    for(int d : s) {
	      vLits.clear();
	      vLits.push_back(-nvars);
	      if(d < 0) {
		vLits.push_back(phead + k*nnodes*nexs + j*nexs - d);
	      }
	      else {
		vLits.push_back((k-1)*nnodes*ndata + j*ndata + d + 1);
		for(int h : incoms[j]) {
		  vLits.push_back(yhead + k*ncoms*ndata + h*ndata + d + 1);
		}
	      }
	      write_clause(nclauses, vLits);
	    }
	    if(nexs) {
	      auto &excond = exconds[i][si];
	      for(auto &e: excond) {
		if(!e.second) {
		  continue;
		}
		vLits.clear();
		vLits.push_back(-nvars);
		vLits.push_back(qhead + e.first + 1);
		write_clause(nclauses, vLits);
	      }
	    }
	  }
	  vLits.clear();
	  vLits.push_back(-(zhead + k*nnodes*ndata + j*ndata + i + 1));
	  for(int l = nvars_ + 1; l <= nvars; l++) {
	    vLits.push_back(l);
	  }
	  write_clause(nclauses, vLits);
	}
	else {
	  for(auto &s : operands[i]) {
	    if(operands[i].size() != 1) {
	      show_error("unexpected error");
	    }
	    for(int d : s) {
	      vLits.clear();
	      vLits.push_back(-(zhead + k*nnodes*ndata + j*ndata + i + 1));
	      if(d < 0) {
		vLits.push_back(phead + k*nnodes*nexs + j*nexs - d);
	      }
	      else {
		vLits.push_back((k-1)*nnodes*ndata + j*ndata + d + 1);
		for(int h : incoms[j]) {
		  vLits.push_back(yhead + k*ncoms*ndata + h*ndata + d + 1);
		}
	      }
	      write_clause(nclauses, vLits);
	    }
	  }
	  if(operands[i].empty()) {
	    vLits.clear();
	    vLits.push_back(-(zhead + k*nnodes*ndata + j*ndata + i + 1));
	    write_clause(nclauses, vLits);
	  }
	}
      }
    }
    for(int j : mems) {
      for(int i = 0; i < ndata; i++) {
	vLits.clear();
	vLits.push_back(-(zhead + k*nnodes*ndata + j*ndata + i + 1));
	write_clause(nclauses, vLits);
      }
    }
  }

  // extra nodes
  for(int k = 0; k < ncycles; k++) {
    for(int j : pes) {
      for(auto &ex: exs) {
	int nc = get<3>(ex).size();
	for(int i = 0; i < nc; i++) {
	  int nvars_ = nvars;
	  for(int ii = 0; ii < nc; ii++) {
	    int d = get<3>(ex)[ii];
	    nvars++;
	    vLits.clear();
	    vLits.push_back(-nvars);	
	    if(d < 0) {
	      vLits.push_back(phead + k*nnodes*nexs + j*nexs - d);
	    }
	    else {
	      vLits.push_back((k-1)*nnodes*ndata + j*ndata + d + 1);
	      for(int h : incoms[j]) {
		vLits.push_back(yhead + k*ncoms*ndata + h*ndata + d + 1);
	      }
	    }
	    write_clause(nclauses, vLits);
	    vLits.clear();
	    vLits.push_back(-nvars);
	    int s = get<2>(ex);
	    if(get<0>(ex)) {
	      s += i * nc + ii;
	    }
	    else {
	      s += (ii - i + nc) % nc;
	    }
	    vLits.push_back(qhead + s + 1);
	    write_clause(nclauses, vLits);
	  }
	  // amo and alo for i
	  for(int i = 0; i < nc; i++) {
	    vLits.clear();
	    for(int ii = 0; ii < nc; ii++) {
	      int s = get<2>(ex) + i * nc + ii;
	      vLits.push_back(qhead + s + 1);
	    }
	    write_clause(nclauses, vLits);
	    cardinality_amo(nvars, nclauses, vLits);
	    if(!get<0>(ex)) {
	      break;
	    }
	  }
	  // amo for ii
	  if(get<0>(ex)) {
	    for(int ii = 0; ii < nc; ii++) {
	      vLits.clear();
	      for(int i = 0; i < nc; i++) {
		int s = get<2>(ex) + i * nc + ii;
		vLits.push_back(qhead + s + 1);
	      }
	      cardinality_amo(nvars, nclauses, vLits);
	    }
	  }
	}
      }
    }
  }

  // at most 1 or K
  f << (nilp? "\\": "c") << " at most 1 or K" << endl;
  if(ncontexts <= 0 || ncontexts > ncycles) {
    ncontexts = ncycles;
  }
  for(int t = 0; t < ncontexts; t++) {
    // reg
    if (nregs > 0) {
      for(int j : pes) {
	vLits.clear();
	for(int k = t+1; k < ncycles; k += ncontexts) {
	  for(int i = 0; i < ndata; i++) {
	    vLits.push_back(k*nnodes*ndata + j*ndata + i + 1);
	  }
	}
	if(nregs == 1) {
	  cardinality_amo(nvars, nclauses, vLits);
	}
	else {
	  cardinality_amk(nvars, nclauses, vLits, nregs);
	}
      }
    }
    // com
    for(int h = 0; h < ncoms; h++) {
      int band = get<2>(coms[h]);
      if(band <= 0) {
	continue;
      }
      vLits.clear();
      for(int k = t+1; k < ncycles; k += ncontexts) {
	for(int i = 0; i < ndata; i++) {
	  vLits.push_back(yhead + k*ncoms*ndata + h*ndata + i + 1);
	}
      }
      if(band == 1) {
	cardinality_amo(nvars, nclauses, vLits);	
      }
      else {
	cardinality_amk(nvars, nclauses, vLits, band);
      }
    }
    // ope
    if(nprocs > 0) {
      for(int j : pes) {
	vLits.clear();
	for(int k = t+1; k < ncycles; k += ncontexts) {
	  for(int i = 0; i < ndata; i++) {
	    vLits.push_back(zhead + k*nnodes*ndata + j*ndata + i + 1);
	  }
	}
	if(nprocs == 1) {
	  cardinality_amo(nvars, nclauses, vLits);
	}
	else {
	  cardinality_amk(nvars, nclauses, vLits, nprocs);
	}
      }
    }
    // memsize
    for(auto j : memsize) {
      if(j.second <= 0) {
	continue;
      }
      vLits.clear();
      for(int k = t+1; k < ncycles; k += ncontexts) {
	for(int i = 0; i < ndata; i++) {
	  vLits.push_back(k*nnodes*ndata + j.first*ndata + i + 1);
	}
      }
      if(j.second == 1) {
	cardinality_amo(nvars, nclauses, vLits);
      }
      else {
	cardinality_amk(nvars, nclauses, vLits, j.second);
      }
    }
    // nports
    for(auto j : nports) {
      // coming
      if (j.second.first > 0) {
	vLits.clear();
	for(int k = t+1; k < ncycles; k += ncontexts) {
	  for(int h : incoms[j.first]) {
	    for(int i = 0; i < ndata; i++) {
	      vLits.push_back(yhead + k*ncoms*ndata + h*ndata + i + 1);
	    }
	  }
	}
	if(j.second.first == 1) {
	  cardinality_amo(nvars, nclauses, vLits);
	}
	else {
	  cardinality_amk(nvars, nclauses, vLits, j.second.first);
	}
      }
      // going
      if (j.second.second > 0) {
	vLits.clear();
	for(int k = t+1; k < ncycles; k += ncontexts) {
	  for(int h : outcoms[j.first]) {
	    for(int i = 0; i < ndata; i++) {
	      vLits.push_back(yhead + k*ncoms*ndata + h*ndata + i + 1);
	    }
	  }
	}
	if(j.second.second == 1) {
	  cardinality_amo(nvars, nclauses, vLits);
	}
	else {
	  cardinality_amk(nvars, nclauses, vLits, j.second.second);
	}
      }
    }
  }
  // amk assign
  for(auto j : amk_assignments) {
    if(get<2>(j) <= 0) {
      continue;
    }
    vLits.clear();
    for(int i : get<1>(j)) {
      vLits.push_back(get<0>(j)*ndata + i + 1);
    }
    if(get<2>(j) == 1) {
      cardinality_amo(nvars, nclauses, vLits);
    }
    else {
      cardinality_amk(nvars, nclauses, vLits, get<2>(j));
    }
  }

  // priority
  if(!priority.empty()) {
    set<int> s;
    for(auto &t : priority) {
      s.insert(get<0>(t));
    }
    map<int, vector<int> > m;
    for(int i : s) {
      for(int k = 0; k < ncycles; k++) {
	nvars++;
	vLits.clear();
	vLits.push_back(-nvars);
	for(int j = 0; j < nnodes; j++) {
	  vLits.push_back(k*nnodes*ndata + j*ndata + i + 1);
	}
	write_clause(nclauses, vLits);
	m[i].push_back(nvars);
      }
    }
    for(auto &t : priority) {
      int i0 = get<0>(t);
      int i1 = get<1>(t);
      for(int k1 = 1; k1 < ncycles; k1++) {
	int k0 = get<2>(t)? k1: k1 - 1;
	for(int j1 : pes) {
	  vLits.clear();
	  vLits.push_back(-(zhead + k1*nnodes*ndata + j1*ndata + i1 + 1));
	  for(int k = 0; k <= k0; k++) {
	    vLits.push_back(m[i0][k]);
	  }
	  write_clause(nclauses, vLits);
	}
      }
    }
  }

  // option
  if(!fextmem) {
    f << (nilp? "\\": "c") << " not fextmem" << endl;
    for(int k = 0; k < ncycles; k++) {
      for(int i = ninputs; i < ndata; i++) {
	if(find(output_ids.begin(), output_ids.end(), i) == output_ids.end()) {
	  // do not have
	  vLits.clear();
	  vLits.push_back(-(k*nnodes*ndata + i + 1));
	  write_clause(nclauses, vLits);
	  // do not send
	  for(int h : outcoms[0]) {
	    vLits.clear();
	    vLits.push_back(-(yhead + k*ncoms*ndata + h*ndata + i + 1));
	    write_clause(nclauses, vLits);
	  }
	  // do not receive
	  for(int h : incoms[0]) {
	    vLits.clear();
	    vLits.push_back(-(yhead + k*ncoms*ndata + h*ndata + i + 1));
	    write_clause(nclauses, vLits);
	  }
	}
      }
    }
  }
  
  if(nilp) {
    f << "binary" << endl;
    for(int i = 0; i < nvars; i++) {
      f << "x" << i+1 << endl;
    }
    f << "end" << endl;
  }
  
  f.close();

  nvars_ = nvars;

  if(nilp) {
    return;
  }
  
  string header = "p cnf " + to_string(nvars) + " " + to_string(nclauses);
  string cmd = "sed -i \'1i" + header + "\' " + filename;
  system(cmd.c_str());
}

void Cnf::gen_image(string filename) {
  vector<bool> results(nvars_);
  if(!nilp) {
    ifstream f(filename);
    if(!f) {
      show_error("cannot open result file", filename);
    }
    string l;
    while(getline(f, l)) {
      if(nilp == 1) {
	string::size_type i = l.find("<");
	string::size_type j = l.find(">");
	if(i == string::npos || j == string::npos || i > j) {
	  continue;
	}
	l = l.substr(i+1, j-i-1);
	if(l == "variables") {
	  while(getline(f, l)) {
	    i = l.find("<");
	    j = l.find(">");
	    if(i == string::npos || j == string::npos || i > j) {
	      continue;
	    }
	    l = l.substr(i+1, j-i-1);
	    if(l == "/variables") {
	      break;
	    }
	    string sname, svalue;
	    string s;
	    stringstream ss(l);
	    try {
	      while(getline(ss, s, ' ')) {
		if(s.find("=") == string::npos) {
		  continue;
		}
		stringstream ss2(s);
		getline(ss2, s, '=');
		if(s == "name") {
		  getline(ss2, s, '=');
		  ss2.clear();
		  ss2.str(s);
		  getline(ss2, s, '\"');
		  getline(ss2, s, '\"');
		  sname = s.substr(1, s.size()-1);
		}
		if(s == "value") {
		  getline(ss2, s, '=');
		  ss2.clear();
		  ss2.str(s);
		  getline(ss2, s, '\"');
		  getline(ss2, s, '\"');
		  svalue = s;
		}
	      }
	      if(str2int(svalue)) {
		results[str2int(sname)-1] = 1;
	      }
	    }
	    catch(...) {
	      show_error("unexpected line", l);
	    }
	  }
	}
	continue;
      }
      if(nilp == 2) {
	if(l.empty() || l[0] == '#') {
	  continue;
	}
	string sname, svalue;
	stringstream ss(l);
	try {
	  getline(ss, sname, ' ');
	  sname = sname.substr(1);
	  getline(ss, svalue, ' ');
	  if(str2int(svalue)) {
	    results[str2int(sname)-1] = 1;
	  }
	}
	catch(...) {
	  show_error("unexpected line", l);
	}
	continue;
      }
      string s;
      stringstream ss(l);
      getline(ss, s, ' ');
      if(s == "1" || s == "-1") {
	if(s == "1") {
	  results[0] = 1;
	}
	while(getline(ss, s, ' ')) {
	  try {
	    int i = str2int(s);
	    if(i > 0) {
	      results[i-1] = 1;
	    }
	  }
	  catch(...) {
	    show_error("unexpected word", s);
	  }
	}
      }
      else if(s == "v") {
	while(getline(ss, s, ' ')) {
	  try {
	    int i = str2int(s);
	    if(i > 0) {
	      results[i-1] = 1;
	    }
	  }
	  catch(...) {
	    show_error("unexpected word", s);
	  }
	}
      }
    }
  }
  
  image.resize(ncycles_, vector<vector<int> >(nnodes + ncoms));
  for(int k = 0; k < ncycles_; k++) {
    for(int j = 0; j < nnodes; j++) {
      for(int i = 0; i < ndata; i++) {
	if(results[k*nnodes*ndata + j*ndata + i]) {
	  image[k][j].push_back(i);
	}
      }
    }
  }
  for(int k = 0; k < ncycles_; k++) {
    for(int h = 0; h < ncoms; h++) {
      for(int i = 0; i < ndata; i++) {
	if(results[yhead + k*ncoms*ndata + h*ndata + i]) {
	  image[k][nnodes+h].push_back(i);
	}
      }
    }
  }

  if(nexs == 0) {
    return;
  }
  exmap.clear();
  for(auto &ex: exs) {
    int nc = get<3>(ex).size();
    for(int i = 0; i < nc; i++) {
      for(int ii = 0; ii < nc; ii++) {
	int s = get<2>(ex);
	if(get<0>(ex)) {
	  s += i * nc + ii;
	}
	else {
	  s += (ii - i + nc) % nc;
	}
	if(results[qhead + s]) {
	  int exid = get<1>(ex) + i;
	  exmap[exid] = get<3>(ex)[ii];
	  while(exmap[exid] < 0) {
	    exmap[exid] = exmap[-exmap[exid]-1];
	  }
	  break;
	}
      }
    }
  }
  for(int i = 0; i < ndata; i++) {
    vector<set<int> > vs;
    for(int j = 0; j < (int)operands[i].size(); j++) {
      bool ff = 0;
      for(auto &e : exconds[i][j]) {
	if(results[qhead + e.first] != e.second) {
	  ff = 1;
	  break;
	}
      }
      if(ff) {
	continue;
      }
      set<int> s;
      for(int k: operands[i][j]) {
	if(k < 0) {
	  s.insert(exmap[-k-1]);
	}
	else {
	  s.insert(k);
	}
      }
      vs.push_back(s);
    }
    operands[i] = vs;
  }
}

void Cnf::reduce_image() {
  vector<vector<vector<int> > > fimage(ncycles_, vector<vector<int> >(nnodes + ncoms));
  for(int k = 0; k < ncycles_; k++) {
    for(int j = 0; j < nnodes + ncoms; j++) {
      fimage[k][j].resize(image[k][j].size());
    }
  }
  // mark output data
  for(int id : output_ids) {
    bool f = 0;
    for(int i = 0; i < (int)image[ncycles_-1][0].size(); i++) {
      if(id == image[ncycles_-1][0][i]) {
	fimage[ncycles_-1][0][i] = 1;
	f = 1;
	break;
      }
    }
    if(!f) {
      show_error("incomplete solution");
    }
  }
  // propagate backwards
  for(int k = ncycles_-1; k > 0; k--) {
    // propagate from mems
    for(int j : mems) {
      for(int i = 0; i < (int)image[k][j].size(); i++) {
	if(!fimage[k][j][i]) {
	  continue;
	}
	int idi = image[k][j][i];
	bool f = 0;
	if(tempnodes.empty() || !tempnodes[j]) {
	  // mark data in mem at previous cycle if possible
	  for(int ii = 0; ii < (int)image[k-1][j].size(); ii++) {
	    int idii = image[k-1][j][ii];
	    if(idi == idii) {
	      fimage[k-1][j][ii] = 1;
	      f = 1;
	      break;
	    }
	  }
	  if(f) {
	    continue;
	  }
	}
	// mark data coming
	for(int h : incoms[j]) {
	  for(int ii = 0; ii < (int)image[k][nnodes+h].size(); ii++) {
	    int idii = image[k][nnodes+h][ii];
	    if(idi == idii) {
	      fimage[k][nnodes+h][ii] = 1;
	      f = 1;
	      break;
	    }
	  }
	  if(f) {
	    break;
	  }
	}
	if(!f) {
	  show_error("incomplete solution");
	}
      }
    }
    // propagate from pes
    for(int j : pes) {
      for(int i = 0; i < (int)image[k][j].size(); i++) {
	if(!fimage[k][j][i]) {
	  continue;
	}
	int idi = image[k][j][i];
	bool f = 0;
	if(tempnodes.empty() || !tempnodes[j]) {
	  // mark data in the pe at previous cycle if possible
	  for(int ii = 0; ii < (int)image[k-1][j].size(); ii++) {
	    int idii = image[k-1][j][ii];
	    if(idi == idii) {
	      fimage[k-1][j][ii] = 1;
	      f = 1;
	      break;
	    }
	  }
	  if(f) {
	    continue;
	  }
	}
	// mark data coming if possible
	for(int h : incoms[j]) {
	  for(int ii = 0; ii < (int)image[k][nnodes+h].size(); ii++) {
	    int idii = image[k][nnodes+h][ii];
	    if(idi == idii) {
	      fimage[k][nnodes+h][ii] = 1;
	      f = 1;
	      break;
	    }
	  }
	  if(f) {
	    break;
	  }
	}
	if(f) {
	  continue;
	}
	// mark data required for the operation
	for(auto &s : operands[idi]) {
	  bool ff = 1;
	  // check if all operands are ready
	  for(auto d : s) {
	    ff = 0;
	    // in the node
	    for(int ii = 0; ii < (int)image[k-1][j].size(); ii++) {
	      int idii = image[k-1][j][ii];
	      if(d == idii) {
		ff = 1;
		break;
	      }
	    }
	    if(ff) {
	      continue;
	    }
	    // coming
	    for(int h : incoms[j]) {
	      for(int ii = 0; ii < (int)image[k][nnodes+h].size(); ii++) {
		int idii = image[k][nnodes+h][ii];
		if(d == idii) {
		  ff = 1;
		  break;
		}
	      }
	      if(ff) {
		break;
	      }
	    }
	    if(ff) {
	      continue;
	    }
	    break;
	  }
	  if(!ff) {
	    continue;
	  }
	  // mark operands
	  for(auto d : s) {
	    ff = 0;
	    // in the node
	    for(int ii = 0; ii < (int)image[k-1][j].size(); ii++) {
	      int idii = image[k-1][j][ii];
	      if(d == idii) {
		fimage[k-1][j][ii] = 1;
		ff = 1;
		break;
	      }
	    }
	    if(ff) {
	      continue;
	    }
	    // coming
	    for(int h : incoms[j]) {
	      for(int ii = 0; ii < (int)image[k][nnodes+h].size(); ii++) {
		int idii = image[k][nnodes+h][ii];
		if(d == idii) {
		  fimage[k][nnodes+h][ii] = 1;
		  ff = 1;
		  break;
		}
	      }
	      if(ff) {
		break;
	      }
	    }
	    if(ff) {
	      continue;
	    }
	    show_error("unexpected error");
	  }
	  f = 1;
	  break;
	}
	if(!f) {
	  show_error("incomplete solution");
	}
      }
    }
    // propagate bypass
    for(int g = 0; g < 2; g++) {
      for(auto h : bypass) {
	for(int i = 0; i < (int)image[k][nnodes+h.first].size(); i++) {
	  if(!fimage[k][nnodes+h.first][i]) {
	    continue;
	  }
	  int idi = image[k][nnodes+h.first][i];
	  bool f = 0;
	  for(int h2 : h.second) {
	    for(int ii = 0; ii < (int)image[k][nnodes+h2].size(); ii++) {
	      int idii = image[k][nnodes+h2][ii];
	      if(idi == idii) {
		fimage[k][nnodes+h2][ii] = 1;
		f = 1;
		break;
	      }
	    }
	    if(f) {
	      break;
	    }
	  }
	}
      }
    }
    // propagate from communication paths
    for(int h = 0; h < ncoms; h++) {
      for(int i = 0; i < (int)image[k][nnodes+h].size(); i++) {
	if(!fimage[k][nnodes+h][i]) {
	  continue;
	}
	int idi = image[k][nnodes+h][i];
	bool f = 0;
	if(bypass.count(h)) {
	  for(int h2 : bypass[h]) {
	    for(int ii = 0; ii < (int)image[k][nnodes+h2].size(); ii++) {
	      int idii = image[k][nnodes+h2][ii];
	      if(idi == idii) {
		f = 1;
		break;
	      }
	    }
	    if(f) {
	      break;
	    }
	  }
	}
	if(f) {
	  continue;
	}
	for(int j : get<0>(coms[h])) {
	  for(int ii = 0; ii < (int)image[k-1][j].size(); ii++) {
	    int idii = image[k-1][j][ii];
	    if(idi == idii) {
	      fimage[k-1][j][ii] = 1;
	      f = 1;
	      break;
	    }
	  }
	}
	if(!f) {
	  show_error("incomplete solution");
	}
      }
    }
  }
  // update image
  vector<vector<vector<int> > > image_old = image;
  for(int k = 0; k < ncycles_; k++) {
    for(int j = 0; j < nnodes + ncoms; j++) {
      image[k][j].clear();
      for(int i = 0; i < (int)image_old[k][j].size(); i++) {
	if(fimage[k][j][i]) {
	  image[k][j].push_back(image_old[k][j][i]);
	}
      }
    }
  }
}

void Cnf::setup_glucose(bool fincr) {
  // Empty function since we don't use Glucose
}

void Cnf::run_glucose_opt() {
  // Empty function since we don't use Glucose  
}
