
from urllib.parse import unquote
import copy
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import bs4


def navpoint_to_dict(navpoint_sp, src_mapping):
  attrs = navpoint_sp.attrs
  label = navpoint_sp.find_all('navlabel')[0].text.rstrip('\n ').lstrip('\n ')
  src = navpoint_sp.find_all('content')[0].attrs['src'].split('#')[0]
  #print(attrs)
  return {
    'id': attrs['id'],
    'cfi_path': src_mapping[src][1],
    'playorder': int(attrs['playorder']),
    'navlabel': label,
    'nav_src': unquote(src),
    'nav_name': src_mapping[src][0]
  }

def get_nav_spine_item(navspine_item, navpoints):
  navpoint = {
    'id': None,
    'cfi_path': navspine_item[1][1],
    'playorder': None,
    'navlabel': None,
    'nav_src': unquote(navspine_item[0]),
    'nav_name': navspine_item[1][0]
  }
  if navspine_item[1][1] in navpoints:
    navpoint = navpoints[navspine_item[1][1]]
  return navpoint

def get_navpoints(book):
  
  src_mapping = {book.get_item_with_id(si[0]).file_name:(si[0], i+1) for i, si in enumerate(book.spine) if si[0] is not None}
  nav_list = list(book.get_items_of_type(ebooklib.ITEM_NAVIGATION))
  if len(nav_list) == 1:
    nav = nav_list[0]
  else:
    nav_list = [it for it in list(book.get_items()) if type(it) == ebooklib.epub.EpubNav]
    if len(nav_list) == 1:
      nav = nav_list[0]
    else:
      raise Exception()
  nav_soup = BeautifulSoup(nav.content.decode(),features='lxml')
  navpoints = nav_soup.find_all('navpoint')
  navpoints = [navpoint_to_dict(np, src_mapping) for np in navpoints]
  np_dict = {}
  for np in navpoints:
    if np['cfi_path'] not in np_dict:
      np_dict[np['cfi_path']] = np
  navpoints = np_dict
  
  navspine = [get_nav_spine_item((k,v), navpoints) for k,v in src_mapping.items()]
  
  return navspine

def build_toc_dict(book, np_src_map):
  toc = book.toc
  
  def gather_toc_items(toc_item, parent):
    items = []
    if type(toc_item) == list:
      for item in toc_item:
        items += gather_toc_items(item, parent)
    elif type(toc_item) == tuple:
      section = toc_item[0]
      items = [{'id':np_src_map[section.href.split('#')[0]], 'parent': parent}]
      items += gather_toc_items(toc_item[1], np_src_map[section.href.split('#')[0]])
    else:
      items = [{'id':np_src_map[toc_item.href.split('#')[0]], 'parent': parent}]
    return items
  
  toc_items = gather_toc_items(toc, None)
  
  toc_dict =  {t_item['id']:{'parent':t_item['parent']} for t_item in toc_items}
  
  def add_children(toc_dict):
    toc_dict_copy = copy.copy(toc_dict)
    toc_items = {}
    for kt, v in toc_dict_copy.items():
      v['children'] = [int(k) for k,v in toc_dict.items() if v['parent'] == kt]
      toc_items[kt] = v

    return toc_items
  
  toc_dict = add_children(toc_dict)
  
  return toc_dict

def get_navigation(book):
  navpoints = get_navpoints(book)
  navpoints = {int(np['cfi_path']):np for np in navpoints}
  np_src_map = {np['nav_src']:idx for idx, np in navpoints.items()}
  toc_dict = build_toc_dict(book, np_src_map)
  navpoints = {k:{**navpoints[k], **toc_dict.get(k, {})} for k,_ in navpoints.items() if k is not None}
  return navpoints, np_src_map, toc_dict



def searchhtml(data):
    return p.search(data)
  
def extract_text_and_html_segments(body_str):
  parts = []
  remaining_text = body_str
  while len(remaining_text) > 0:
    match = searchhtml(remaining_text)
    if match is not None:
      span = match.span()
      if span[0] > 0:
        parts.append({'content':remaining_text[0:span[0]], 'type':'text'})
      parts.append({'content':remaining_text[span[0]:span[1]], 'type':'html'})
      remaining_text = remaining_text[span[1]:]
    else:
      parts.append({'content':remaining_text, 'type':'text'})
      remaining_text = ''
  return parts

def get_clean_soup_children(parent):
  return [p for p in list(parent.children) if p != '\n']



def collect_path(path_children, elem_list=None, current_path='/', tag_parents=''):
  if elem_list is None:
    elem_list = []
  for i, child in enumerate(path_children):
    if type(child) == bs4.element.Tag:
      elem_list += collect_path(get_clean_soup_children(child), [], current_path+str((i+1)*2)+'/', tag_parents+'/'+child.name)
    elif type(child) == bs4.element.NavigableString:
      elem_list.append((child, current_path+str(((i)*2)+1), tag_parents))
  return elem_list

def strip_end(text, suffix):
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]

def strip_start(text, prefix):
    if not text.startswith(prefix):
        return text
    return text[len(prefix):]
  
def get_part_words(stcp):
  if type(stcp) == list:
    return [get_part_words(stcp_p) for stcp_p in stcp]
  st, cpath, tag_p = stcp
  text_clean = st.lstrip().rstrip()
  current_pos = 0
  proc_text_parts = []



  text_parts = text_clean.split(' ')
  for tp in text_parts:
    #if len(tp) > 0:
      proc_text_parts.append({'w':tp, 'cfi':cpath+':'+str(current_pos), 'cfi_end':cpath+':'+str(current_pos+len(tp)), 'tp':tag_p})
      current_pos += (len(tp)+1)
  return proc_text_parts

def flatten_list_list(list_list):
  l = []
  for _l in list_list:
    if type(_l) == list:
      l += flatten_list_list(_l)
    else:
      l.append(_l)
  return l

def clean_tp_path(tp_path):
  return ''.join([pp for pp in tp_path.split('/') if pp not in ['div', 'em', 'span', 'b', 'i']])

sentence_end_patt =  re.compile(r'[.?!:;]')

def find_sentence_ids(part_words_flat, current_sentence=0):
  
  pwf_sp = [(pw, clean_tp_path(pw['tp'])) for pw in part_words_flat]
  pws = []
  if len(pwf_sp) == 0:
    return [], current_sentence
  current_sentence_path = pwf_sp[0][1]
  for pw, spath in pwf_sp:
    incr = False
    if spath not in current_sentence_path:
      incr = True
      current_sentence += 1
    nd = {**pw, **{'sid':current_sentence}}
    nd['cfi'] = strip_end(nd['cfi'], '/1:0')
    del nd['tp']
    pws.append(nd)
    if sentence_end_patt.findall(pw['w']) and not incr:
      incr = True
      current_sentence += 1
    current_sentence_path = spath
  return pws, current_sentence


def process_navpoint(book,navpoint, current_senctence_id=0):
  content = BeautifulSoup(book.get_item_with_href(navpoint['nav_src']).content,features='lxml').prettify()
  root = [p for p in list(BeautifulSoup(content,features='lxml').html) if p != '\n']
  parts = [collect_path(get_clean_soup_children(p), current_path='/6/%d[%s]!/%d/' % (navpoint['cfi_path']*2, navpoint['nav_name'], (i+1)*2)) for i, p in enumerate(root)]
  #print(parts)
  part_words = [get_part_words(stcp) for stcp in parts[1:]]
  part_words = flatten_list_list(part_words)
  return find_sentence_ids(part_words, current_senctence_id)



def process_book(book):
  #We get the navpoints and their source (htmlish files)
  navpoints, src_mapping, toc_dict = get_navigation(book)
  current_sentence = 0
  words = []
  for npk in sorted(list(navpoints.keys())):
    #For every file in the book we parse it out and generate CFI bookmarks per word
    navpoint = navpoints[npk]
    new_words, current_sentence = process_navpoint(book,navpoint, current_sentence)
    words += [{**w, **{'p': npk}} for w in new_words]
    current_sentence += 1
  return words, navpoints, src_mapping#, toc_dict
