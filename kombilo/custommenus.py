# File: custommenus.py

##   Copyright (C) 2001-12 Ulrich Goertz (ug@geometry)

##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2 of the License, or
##   (at your option) any later version.

##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

##   You should have received a copy of the GNU General Public License
##   along with this program (see doc/license.txt); if not, write to the Free Software
##   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##   The GNU GPL is also currently available at
##   http://www.gnu.org/copyleft/gpl.html

import cPickle
import os
from Tkinter import Menu, Toplevel, Button, Frame, Label, StringVar, IntVar, Entry, Checkbutton
from tkMessageBox import showinfo
from Tkconstants import *
import v
from libkombilo import SGFError

import __builtin__
if not '_' in __builtin__.__dict__:
    _ = lambda s: s


class CustomMenus:

    def __init__(self, master):
        self.mainMenu = master.mainMenu
        self.master = master
        self.htmlpath = os.curdir
        self.windowOpen = 0
        self.path = v.get_configfile_directory()

    def compare(self, entry1, entry2):
        if entry1['name'] < entry2['name']:
            return -1
        elif entry1['name'] == entry2['name']:
            return 0
        elif entry1['name'] > entry2['name']:
            return 1

    def buildMenus(self, reload=1, alternativePath=''):
        """
        format of menuList entries:
        { 'name' : name (which will be displayed in the menu),
          'entries': [list of entries]
          'subm' : [list of submenus]  }

        format of entry:
        { 'name' : name which will be displayed in the menu,
          'file' : name of a html file which will be displayed upon clicking
                   this entry (or empty),
          'gisearch' : parameters of a game info search to be done when
                       this is chosen,
          'psearch' : pattern and options for a pattern search }

        format of submenu: {} as in menuList
        """

        if reload:

            fallback = "(lp1\n(dp2\nS'subm'\np3\n(lp4\nsS'name'\np5\nS'Fuseki'\np6\nsS'entries'\np7\n(lp8\n(dp9\nS'gisearch'\np10\n(tsS'reset'\np11\nI1\nsS'psearch'\np12\n(((I0\nI0\ntp13\n(I18\nI18\ntt(dp14\n(I7\nI3\ntp15\nS'.'\ns(I16\nI9\ntp16\nS'.'\ns(I8\nI5\ntp17\nS'.'\ns(I9\nI0\ntp18\nS'.'\ns(I-1\nI14\ntp19\nS'.'\ns(I10\nI7\ntp20\nS'.'\ns(I0\nI17\ntp21\nS'.'\ns(I14\nI1\ntp22\nS'.'\ns(I12\nI17\ntp23\nS'.'\ns(I-1\nI16\ntp24\nS'.'\ns(I15\nI4\ntp25\nS'.'\ns(I3\nI2\ntp26\nS'.'\ns(I4\nI5\ntp27\nS'.'\ns(I2\nI2\ntp28\nS'O'\ns(I16\nI0\ntp29\nS'.'\ns(I17\nI13\ntp30\nS'.'\ns(I8\nI12\ntp31\nS'.'\ns(I16\nI-1\ntp32\nS'.'\ns(I9\nI9\ntp33\nS'.'\ns(I10\nI14\ntp34\nS'.'\ns(I11\nI15\ntp35\nS'.'\ns(I14\nI8\ntp36\nS'.'\ns(I12\nI8\ntp37\nS'.'\ns(I15\nI13\ntp38\nS'.'\ns(I13\nI13\ntp39\nS'.'\ns(I0\nI14\ntp40\nS'.'\ns(I3\nI11\ntp41\nS'.'\ns(I1\nI15\ntp42\nS'.'\ns(I4\nI12\ntp43\nS'.'\ns(I2\nI12\ntp44\nS'.'\ns(I5\nI1\ntp45\nS'.'\ns(I3\nI17\ntp46\nS'.'\ns(I16\nI7\ntp47\nS'.'\ns(I6\nI14\ntp48\nS'.'\ns(I17\nI6\ntp49\nS'.'\ns(I7\nI15\ntp50\nS'.'\ns(I10\nI9\ntp51\nS'.'\ns(I11\nI4\ntp52\nS'.'\ns(I12\nI7\ntp53\nS'.'\ns(I-1\nI2\ntp54\nS'.'\ns(I15\nI10\ntp55\nS'.'\ns(I13\nI6\ntp56\nS'.'\ns(I0\nI5\ntp57\nS'.'\ns(I1\nI0\ntp58\nS'.'\ns(I4\nI11\ntp59\nS'.'\ns(I2\nI7\ntp60\nS'.'\ns(I5\nI10\ntp61\nS'.'\ns(I6\nI1\ntp62\nS'.'\ns(I4\nI17\ntp63\nS'.'\ns(I7\nI4\ntp64\nS'.'\ns(I17\nI17\ntp65\nS'.'\ns(I8\nI0\ntp66\nS'.'\ns(I-1\nI5\ntp67\nS'.'\ns(I1\nI-1\ntp68\nS'.'\ns(I16\nI11\ntp69\nS'.'\ns(I17\nI10\ntp70\nS'.'\ns(I8\nI7\ntp71\nS'.'\ns(I9\nI6\ntp72\nS'.'\ns(I-1\nI12\ntp73\nS'.'\ns(I10\nI5\ntp74\nS'.'\ns(I11\nI8\ntp75\nS'.'\ns(I14\nI7\ntp76\nS'.'\ns(I15\nI6\ntp77\nS'.'\ns(I0\nI9\ntp78\nS'.'\ns(I3\nI4\ntp79\nS'.'\ns(I4\nI7\ntp80\nS'.'\ns(I10\nI-1\ntp81\nS'.'\ns(I5\nI6\ntp82\nS'.'\ns(I16\nI2\ntp83\nS'.'\ns(I17\nI3\ntp84\nS'.'\ns(I7\nI16\ntp85\nS'.'\ns(I8\nI14\ntp86\nS'.'\ns(I9\nI15\ntp87\nS'.'\ns(I10\nI12\ntp88\nS'.'\ns(I11\nI1\ntp89\nS'.'\ns(I9\nI17\ntp90\nS'.'\ns(I14\nI14\ntp91\nS'O'\ns(I12\nI10\ntp92\nS'.'\ns(I15\nI15\ntp93\nS'.'\ns(I13\nI11\ntp94\nS'.'\ns(I2\nI16\ntp95\nS'.'\ns(I0\nI0\ntp96\nS'.'\ns(I3\nI13\ntp97\nS'.'\ns(I1\nI13\ntp98\nS'.'\ns(I4\nI14\ntp99\nS'.'\ns(I2\nI10\ntp100\nS'.'\ns(I5\nI15\ntp101\nS'.'\ns(I9\nI-1\ntp102\nS'.'\ns(I6\nI12\ntp103\nS'.'\ns(I17\nI4\ntp104\nS'.'\ns(I7\nI9\ntp105\nS'.'\ns(I11\nI6\ntp106\nS'.'\ns(I14\nI17\ntp107\nS'.'\ns(I12\nI1\ntp108\nS'.'\ns(I-1\nI0\ntp109\nS'.'\ns(I10\nI17\ntp110\nS'.'\ns(I13\nI4\ntp111\nS'.'\ns(I0\nI7\ntp112\nS'.'\ns(I1\nI6\ntp113\nS'.'\ns(I2\nI5\ntp114\nS'.'\ns(I5\nI8\ntp115\nS'.'\ns(I6\nI7\ntp116\nS'.'\ns(I7\nI6\ntp117\nS'.'\ns(I8\nI2\ntp118\nS'.'\ns(I9\nI3\ntp119\nS'.'\ns(I-1\nI11\ntp120\nS'.'\ns(I14\nI2\ntp121\nS'X'\ns(I3\nI1\ntp122\nS'.'\ns(I16\nI13\ntp123\nS'.'\ns(I6\nI16\ntp124\nS'.'\ns(I17\nI8\ntp125\nS'.'\ns(I17\nI-1\ntp126\nS'.'\ns(I8\nI9\ntp127\nS'.'\ns(I9\nI4\ntp128\nS'.'\ns(I10\nI3\ntp129\nS'.'\ns(I4\nI-1\ntp130\nS'.'\ns(I11\nI10\ntp131\nS'.'\ns(I14\nI5\ntp132\nS'.'\ns(I12\nI13\ntp133\nS'.'\ns(I1\nI16\ntp134\nS'.'\ns(I15\nI0\ntp135\nS'.'\ns(I13\nI16\ntp136\nS'.'\ns(I0\nI11\ntp137\nS'.'\ns(I3\nI6\ntp138\nS'.'\ns(I1\nI10\ntp139\nS'.'\ns(I4\nI1\ntp140\nS'.'\ns(I5\nI4\ntp141\nS'.'\ns(I16\nI4\ntp142\nS'.'\ns(I6\nI11\ntp143\nS'.'\ns(I17\nI1\ntp144\nS'.'\ns(I9\nI13\ntp145\nS'.'\ns(I10\nI10\ntp146\nS'.'\ns(I11\nI3\ntp147\nS'.'\ns(I3\nI-1\ntp148\nS'.'\ns(I14\nI12\ntp149\nS'.'\ns(I12\nI4\ntp150\nS'.'\ns(I15\nI9\ntp151\nS'.'\ns(I13\nI9\ntp152\nS'.'\ns(I0\nI2\ntp153\nS'.'\ns(I3\nI15\ntp154\nS'.'\ns(I1\nI3\ntp155\nS'.'\ns(I4\nI8\ntp156\nS'.'\ns(I2\nI8\ntp157\nS'.'\ns(I5\nI13\ntp158\nS'.'\ns(I6\nI2\ntp159\nS'.'\ns(I7\nI11\ntp160\nS'.'\ns(I16\nI17\ntp161\nS'.'\ns(I12\nI3\ntp162\nS'.'\ns(I-1\nI6\ntp163\nS'.'\ns(I13\nI2\ntp164\nS'.'\ns(I1\nI4\ntp165\nS'.'\ns(I2\nI3\ntp166\nS'.'\ns(I12\nI-1\ntp167\nS'.'\ns(I6\nI5\ntp168\nS'.'\ns(I7\nI0\ntp169\nS'.'\ns(I5\nI16\ntp170\nS'.'\ns(I16\nI8\ntp171\nS'.'\ns(I8\nI4\ntp172\nS'.'\ns(I9\nI1\ntp173\nS'.'\ns(I-1\nI9\ntp174\nS'.'\ns(I10\nI6\ntp175\nS'.'\ns(I0\nI16\ntp176\nS'.'\ns(I14\nI0\ntp177\nS'.'\ns(I12\nI16\ntp178\nS'.'\ns(I15\nI5\ntp179\nS'.'\ns(I3\nI3\ntp180\nS'.'\ns(I11\nI-1\ntp181\nS'.'\ns(I4\nI4\ntp182\nS'.'\ns(I16\nI15\ntp183\nS'.'\ns(I17\nI14\ntp184\nS'.'\ns(I8\nI11\ntp185\nS'.'\ns(I9\nI10\ntp186\nS'.'\ns(I10\nI1\ntp187\nS'.'\ns(I8\nI17\ntp188\nS'.'\ns(I11\nI12\ntp189\nS'.'\ns(I14\nI11\ntp190\nS'.'\ns(I12\nI15\ntp191\nS'.'\ns(I15\nI2\ntp192\nS'.'\ns(I13\nI14\ntp193\nS'.'\ns(I0\nI13\ntp194\nS'.'\ns(I3\nI8\ntp195\nS'.'\ns(I1\nI8\ntp196\nS'.'\ns(I4\nI3\ntp197\nS'.'\ns(I2\nI15\ntp198\nS'.'\ns(I5\nI2\ntp199\nS'.'\ns(I16\nI6\ntp200\nS'.'\ns(I6\nI9\ntp201\nS'.'\ns(I17\nI7\ntp202\nS'.'\ns(I7\nI12\ntp203\nS'.'\ns(I10\nI8\ntp204\nS'.'\ns(I11\nI5\ntp205\nS'.'\ns(I12\nI6\ntp206\nS'.'\ns(I15\nI11\ntp207\nS'.'\ns(I13\nI7\ntp208\nS'.'\ns(I0\nI4\ntp209\nS'.'\ns(I1\nI1\ntp210\nS'.'\ns(I4\nI10\ntp211\nS'.'\ns(I2\nI6\ntp212\nS'.'\ns(I5\nI11\ntp213\nS'.'\ns(I6\nI0\ntp214\nS'.'\ns(I4\nI16\ntp215\nS'.'\ns(I7\nI5\ntp216\nS'.'\ns(I6\nI-1\ntp217\nS'.'\ns(I-1\nI4\ntp218\nS'.'\ns(I15\nI16\ntp219\nS'.'\ns(I13\nI0\ntp220\nS'.'\ns(I11\nI16\ntp221\nS'.'\ns(I2\nI1\ntp222\nS'.'\ns(I7\nI2\ntp223\nS'.'\ns(I16\nI10\ntp224\nS'.'\ns(I17\nI11\ntp225\nS'.'\ns(I8\nI6\ntp226\nS'.'\ns(I9\nI7\ntp227\nS'.'\ns(I5\nI-1\ntp228\nS'.'\ns(I2\nI-1\ntp229\nS'.'\ns(I-1\nI15\ntp230\nS'.'\ns(I10\nI4\ntp231\nS'.'\ns(I11\nI9\ntp232\nS'.'\ns(I14\nI6\ntp233\nS'.'\ns(I-1\nI17\ntp234\nS'.'\ns(I15\nI7\ntp235\nS'.'\ns(I0\nI8\ntp236\nS'.'\ns(I3\nI5\ntp237\nS'.'\ns(I4\nI6\ntp238\nS'.'\ns(I5\nI7\ntp239\nS'.'\ns(I16\nI1\ntp240\nS'.'\ns(I17\nI12\ntp241\nS'.'\ns(I7\nI17\ntp242\nS'.'\ns(I8\nI13\ntp243\nS'.'\ns(I9\nI8\ntp244\nS'.'\ns(I10\nI15\ntp245\nS'.'\ns(I11\nI14\ntp246\nS'.'\ns(I14\nI9\ntp247\nS'.'\ns(I12\nI9\ntp248\nS'.'\ns(I15\nI12\ntp249\nS'.'\ns(I13\nI12\ntp250\nS'.'\ns(I0\nI15\ntp251\nS'.'\ns(I14\nI-1\ntp252\nS'.'\ns(I3\nI10\ntp253\nS'.'\ns(I1\nI14\ntp254\nS'.'\ns(I4\nI13\ntp255\nS'.'\ns(I2\nI13\ntp256\nS'.'\ns(I5\nI0\ntp257\nS'.'\ns(I3\nI16\ntp258\nS'.'\ns(I6\nI15\ntp259\nS'.'\ns(I17\nI5\ntp260\nS'.'\ns(I7\nI14\ntp261\nS'.'\ns(I11\nI7\ntp262\nS'.'\ns(I14\nI16\ntp263\nS'.'\ns(I12\nI0\ntp264\nS'.'\ns(I-1\nI3\ntp265\nS'.'\ns(I10\nI16\ntp266\nS'.'\ns(I13\nI5\ntp267\nS'.'\ns(I0\nI6\ntp268\nS'.'\ns(I1\nI7\ntp269\nS'.'\ns(I13\nI-1\ntp270\nS'.'\ns(I2\nI4\ntp271\nS'.'\ns(I5\nI9\ntp272\nS'.'\ns(I6\nI6\ntp273\nS'.'\ns(I7\nI7\ntp274\nS'.'\ns(I17\nI16\ntp275\nS'.'\ns(I8\nI1\ntp276\nS'.'\ns(I-1\nI10\ntp277\nS'.'\ns(I16\nI12\ntp278\nS'.'\ns(I17\nI9\ntp279\nS'.'\ns(I8\nI8\ntp280\nS'.'\ns(I9\nI5\ntp281\nS'.'\ns(I-1\nI13\ntp282\nS'.'\ns(I10\nI2\ntp283\nS'.'\ns(I11\nI11\ntp284\nS'.'\ns(I14\nI4\ntp285\nS'.'\ns(I12\nI12\ntp286\nS'.'\ns(I1\nI17\ntp287\nS'.'\ns(I15\nI1\ntp288\nS'.'\ns(I13\nI17\ntp289\nS'.'\ns(I0\nI10\ntp290\nS'.'\ns(I3\nI7\ntp291\nS'.'\ns(I1\nI11\ntp292\nS'.'\ns(I4\nI0\ntp293\nS'.'\ns(I5\nI5\ntp294\nS'.'\ns(I16\nI3\ntp295\nS'.'\ns(I6\nI10\ntp296\nS'.'\ns(I17\nI2\ntp297\nS'.'\ns(I8\nI15\ntp298\nS'.'\ns(I9\nI14\ntp299\nS'.'\ns(I10\nI13\ntp300\nS'.'\ns(I11\nI0\ntp301\nS'.'\ns(I9\nI16\ntp302\nS'.'\ns(I14\nI15\ntp303\nS'.'\ns(I12\nI11\ntp304\nS'.'\ns(I15\nI14\ntp305\nS'.'\ns(I13\nI10\ntp306\nS'.'\ns(I2\nI17\ntp307\nS'.'\ns(I0\nI1\ntp308\nS'.'\ns(I3\nI12\ntp309\nS'.'\ns(I1\nI12\ntp310\nS'.'\ns(I4\nI15\ntp311\nS'.'\ns(I2\nI11\ntp312\nS'.'\ns(I5\nI14\ntp313\nS'.'\ns(I6\nI13\ntp314\nS'.'\ns(I7\nI8\ntp315\nS'.'\ns(I16\nI16\ntp316\nS'.'\ns(I7\nI-1\ntp317\nS'.'\ns(I12\nI2\ntp318\nS'.'\ns(I-1\nI1\ntp319\nS'.'\ns(I13\nI3\ntp320\nS'.'\ns(I1\nI5\ntp321\nS'.'\ns(I-1\nI-1\ntp322\nS'.'\ns(I6\nI4\ntp323\nS'.'\ns(I7\nI1\ntp324\nS'.'\ns(I5\nI17\ntp325\nS'.'\ns(I8\nI3\ntp326\nS'.'\ns(I9\nI2\ntp327\nS'.'\ns(I-1\nI8\ntp328\nS'.'\ns(I14\nI3\ntp329\nS'.'\ns(I0\nI-1\ntp330\nS'.'\ns(I3\nI0\ntp331\nS'.'\ns(I16\nI14\ntp332\nS'.'\ns(I6\nI17\ntp333\nS'.'\ns(I17\nI15\ntp334\nS'.'\ns(I8\nI10\ntp335\nS'.'\ns(I9\nI11\ntp336\nS'.'\ns(I10\nI0\ntp337\nS'.'\ns(I8\nI16\ntp338\nS'.'\ns(I11\nI13\ntp339\nS'.'\ns(I14\nI10\ntp340\nS'.'\ns(I12\nI14\ntp341\nS'.'\ns(I15\nI3\ntp342\nS'.'\ns(I15\nI-1\ntp343\nS'.'\ns(I13\nI15\ntp344\nS'.'\ns(I0\nI12\ntp345\nS'.'\ns(I3\nI9\ntp346\nS'.'\ns(I1\nI9\ntp347\nS'.'\ns(I4\nI2\ntp348\nS'.'\ns(I2\nI14\ntp349\nS'X'\ns(I5\nI3\ntp350\nS'.'\ns(I16\nI5\ntp351\nS'.'\ns(I6\nI8\ntp352\nS'.'\ns(I17\nI0\ntp353\nS'.'\ns(I7\nI13\ntp354\nS'.'\ns(I9\nI12\ntp355\nS'.'\ns(I10\nI11\ntp356\nS'.'\ns(I11\nI2\ntp357\nS'.'\ns(I14\nI13\ntp358\nS'.'\ns(I12\nI5\ntp359\nS'.'\ns(I15\nI8\ntp360\nS'.'\ns(I13\nI8\ntp361\nS'.'\ns(I0\nI3\ntp362\nS'.'\ns(I3\nI14\ntp363\nS'.'\ns(I1\nI2\ntp364\nS'.'\ns(I4\nI9\ntp365\nS'.'\ns(I2\nI9\ntp366\nS'.'\ns(I5\nI12\ntp367\nS'.'\ns(I6\nI3\ntp368\nS'.'\ns(I8\nI-1\ntp369\nS'.'\ns(I7\nI10\ntp370\nS'.'\ns(I-1\nI7\ntp371\nS'.'\ns(I15\nI17\ntp372\nS'.'\ns(I13\nI1\ntp373\nS'.'\ns(I11\nI17\ntp374\nS'.'\ns(I2\nI0\ntp375\nS'.'\nsI0\nI1\nI250\nI0\ntp376\nsg5\nS'Diagonal hoshi'\np377\nsS'file'\np378\nS''\nsa(dp379\ng10\n(tsg11\nI1\nsg12\n(((I10\nI0\nt(I18\nI18\nttp380\n(dp381\n(I6\nI9\ntp382\nS'.'\ns(I11\nI11\ntp383\nS'.'\ns(I10\nI17\ntp384\nS'.'\ns(I7\nI12\ntp385\nS'.'\ns(I12\nI12\ntp386\nS'.'\ns(I1\nI17\ntp387\nS'.'\ns(I13\nI17\ntp388\nS'.'\ns(I14\nI17\ntp389\nS'.'\ns(I0\nI10\ntp390\nS'.'\ns(I1\nI11\ntp391\nS'.'\ns(I-1\nI14\ntp392\nS'.'\ns(I6\nI10\ntp393\nS'.'\ns(I0\nI17\ntp394\nS'.'\ns(I15\nI11\ntp395\nS'.'\ns(I12\nI17\ntp396\nS'.'\ns(I-1\nI16\ntp397\nS'.'\ns(I8\nI15\ntp398\nS'.'\ns(I4\nI10\ntp399\nS'.'\ns(I9\nI14\ntp400\nS'.'\ns(I16\nI15\ntp401\nS'.'\ns(I5\nI11\ntp402\nS'.'\ns(I10\nI13\ntp403\nS'.'\ns(I4\nI16\ntp404\nS'.'\ns(I-1\nI11\ntp405\nS'.'\ns(I9\nI16\ntp406\nS'.'\ns(I14\nI15\ntp407\nS'.'\ns(I12\nI11\ntp408\nS'.'\ns(I17\nI13\ntp409\nS'.'\ns(I15\nI14\ntp410\nS'.'\ns(I13\nI10\ntp411\nS'.'\ns(I2\nI17\ntp412\nS'.'\ns(I3\nI12\ntp413\nS'.'\ns(I1\nI12\ntp414\nS'.'\ns(I8\nI12\ntp415\nS'.'\ns(I4\nI15\ntp416\nS'.'\ns(I2\nI11\ntp417\nS'.'\ns(I9\nI9\ntp418\nS'.'\ns(I5\nI14\ntp419\nS'.'\ns(I10\nI14\ntp420\nS'.'\ns(I6\nI13\ntp421\nS'.'\ns(I11\nI15\ntp422\nS'.'\ns(I15\nI16\ntp423\nS'.'\ns(I6\nI16\ntp424\nS'.'\ns(I11\nI16\ntp425\nS'.'\ns(I15\nI13\ntp426\nS'.'\ns(I13\nI13\ntp427\nS'.'\ns(I0\nI14\ntp428\nS'.'\ns(I3\nI11\ntp429\nS'.'\ns(I1\nI15\ntp430\nS'.'\ns(I8\nI9\ntp431\nS'.'\ns(I4\nI12\ntp432\nS'.'\ns(I2\nI12\ntp433\nS'.'\ns(I16\nI14\ntp434\nS'.'\ns(I3\nI17\ntp435\nS'.'\ns(I14\nI9\ntp436\nS'.'\ns(I6\nI14\ntp437\nS'.'\ns(I11\nI10\ntp438\nS'.'\ns(I7\nI15\ntp439\nS'.'\ns(I12\nI13\ntp440\nS'.'\ns(I1\nI16\ntp441\nS'.'\ns(I17\nI11\ntp442\nS'.'\ns(I13\nI16\ntp443\nS'.'\ns(I0\nI11\ntp444\nS'.'\ns(I16\nI9\ntp445\nS'.'\ns(I1\nI10\ntp446\nS'.'\ns(I10\nI9\ntp447\nS'.'\ns(I16\nI17\ntp448\nS'.'\ns(I-1\nI15\ntp449\nS'.'\ns(I6\nI11\ntp450\nS'.'\ns(I5\nI17\ntp451\nS'.'\ns(I11\nI9\ntp452\nS'.'\ns(I15\nI10\ntp453\nS'.'\ns(I-1\nI17\ntp454\nS'.'\ns(I4\nI11\ntp455\nS'.'\ns(I9\nI13\ntp456\nS'.'\ns(I5\nI10\ntp457\nS'.'\ns(I10\nI10\ntp458\nS'.'\ns(I16\nI13\ntp459\nS'.'\ns(I4\nI17\ntp460\nS'.'\ns(I14\nI12\ntp461\nS'.'\ns(I17\nI12\ntp462\nS'.'\ns(I7\nI17\ntp463\nS'.'\ns(I13\nI9\ntp464\nS'.'\ns(I17\nI17\ntp465\nS'.'\ns(I3\nI15\ntp466\nS'.'\ns(I8\nI13\ntp467\nS'.'\ns(I5\nI13\ntp468\nS'.'\ns(I10\nI15\ntp469\nS'.'\ns(I16\nI16\ntp470\nS'.'\ns(I11\nI14\ntp471\nS'.'\ns(I7\nI11\ntp472\nS'.'\ns(I6\nI17\ntp473\nS'.'\ns(I12\nI9\ntp474\nS'.'\ns(I17\nI15\ntp475\nS'.'\ns(I15\nI12\ntp476\nS'.'\ns(I13\nI12\ntp477\nS'.'\ns(I0\nI15\ntp478\nS'.'\ns(I3\nI10\ntp479\nS'.'\ns(I1\nI14\ntp480\nS'.'\ns(I8\nI10\ntp481\nS'.'\ns(I4\nI13\ntp482\nS'.'\ns(I2\nI13\ntp483\nS'.'\ns(I9\nI11\ntp484\nS'.'\ns(I3\nI16\ntp485\nS'.'\ns(I8\nI16\ntp486\nS'.'\ns(I6\nI15\ntp487\nS'.'\ns(I11\nI13\ntp488\nS'.'\ns(I16\nI10\ntp489\nS'.'\ns(I7\nI14\ntp490\nS'.'\ns(I14\nI10\ntp491\nS'.'\ns(I12\nI14\ntp492\nS'.'\ns(I17\nI10\ntp493\nS'.'\ns(I13\nI15\ntp494\nS'.'\ns(I0\nI12\ntp495\nS'.'\ns(I3\nI9\ntp496\nS'.'\ns(I1\nI9\ntp497\nS'.'\ns(I2\nI14\ntp498\nS'X'\ns(I-1\nI12\ntp499\nS'.'\ns(I14\nI16\ntp500\nS'.'\ns(I5\nI16\ntp501\nS'.'\ns(I10\nI16\ntp502\nS'.'\ns(I7\nI13\ntp503\nS'.'\ns(I15\nI17\ntp504\nS'.'\ns(I0\nI9\ntp505\nS'.'\ns(I9\nI12\ntp506\nS'.'\ns(I5\nI9\ntp507\nS'.'\ns(I10\nI11\ntp508\nS'.'\ns(I-1\nI9\ntp509\nS'.'\ns(I16\nI11\ntp510\nS'.'\ns(I14\nI13\ntp511\nS'.'\ns(I0\nI16\ntp512\nS'.'\ns(I7\nI16\ntp513\nS'.'\ns(I12\nI16\ntp514\nS'.'\ns(I17\nI16\ntp515\nS'.'\ns(I3\nI14\ntp516\nS'.'\ns(I8\nI14\ntp517\nS'X'\ns(I4\nI9\ntp518\nS'.'\ns(I2\nI9\ntp519\nS'.'\ns(I9\nI15\ntp520\nS'.'\ns(I5\nI12\ntp521\nS'.'\ns(I10\nI12\ntp522\nS'.'\ns(I-1\nI10\ntp523\nS'.'\ns(I9\nI17\ntp524\nS'.'\ns(I7\nI10\ntp525\nS'.'\ns(I14\nI14\ntp526\nS'X'\ns(I12\nI10\ntp527\nS'.'\ns(I17\nI14\ntp528\nS'.'\ns(I15\nI15\ntp529\nS'.'\ns(I13\nI11\ntp530\nS'.'\ns(I16\nI12\ntp531\nS'.'\ns(I2\nI16\ntp532\nS'.'\ns(I3\nI13\ntp533\nS'.'\ns(I1\nI13\ntp534\nS'.'\ns(I8\nI11\ntp535\nS'.'\ns(I15\nI9\ntp536\nS'.'\ns(I4\nI14\ntp537\nS'.'\ns(I2\nI10\ntp538\nS'.'\ns(I9\nI10\ntp539\nS'.'\ns(I5\nI15\ntp540\nS'.'\ns(I8\nI17\ntp541\nS'.'\ns(I6\nI12\ntp542\nS'.'\ns(I11\nI12\ntp543\nS'.'\ns(I7\nI9\ntp544\nS'.'\ns(I14\nI11\ntp545\nS'.'\ns(I12\nI15\ntp546\nS'.'\ns(I11\nI17\ntp547\nS'.'\ns(I17\nI9\ntp548\nS'.'\ns(I13\nI14\ntp549\nS'.'\ns(I0\nI13\ntp550\nS'.'\ns(I2\nI15\ntp551\nS'.'\ns(I-1\nI13\ntp552\nS'.'\nsI0\nI0\nI250\nI0\ntp553\nsg5\nS'San ren sei'\np554\nsg378\nS''\nsasa(dp555\ng3\n(lp556\nsg5\nS'Players'\np557\nsg7\n(lp558\n(dp559\ng10\n(S''\nS''\nS'Cho U'\nS''\nS''\nS''\nS''\nI0\ntp560\nsg11\nI1\nsg12\n(tsg5\nS'Cho U'\np561\nsg378\nS''\nsa(dp562\ng10\n(S''\nS''\nS'Go Seigen'\nS''\nS''\nS''\nS''\nI0\ntp563\nsg11\nI1\nsg12\n(tsg5\nS'Go Seigen'\np564\nsg378\nS''\nsasa."

            try:
                file = open(os.path.join(self.path, 'menus.def'))
                self.customMenuList = cPickle.load(file)
                file.close()
            except IOError:
                if alternativePath:
                    try:
                        file = open(os.path.join(alternativePath, 'menus.def'))
                        self.customMenuList = cPickle.load(file)
                        file.close()
                    except IOError:
                        self.customMenuList = cPickle.loads(fallback)
                else:
                    self.customMenuList = cPickle.loads(fallback)

        self.noOfMenus = len(self.customMenuList)

        # build menus

        self.customMenuCommands = []
        self.mmIndex = 3
        self.customMenuList.sort(self.compare)

        for item in self.customMenuList:
            m = Menu(self.mainMenu)
            self.mainMenu.insert_cascade(self.mmIndex, menu=m, label=item['name'])
            self.mmIndex += 1

            self.addMenu(item['subm'], m)
            item['entries'].sort(self.compare)

            for e in item['entries']:
                m.add_command(label=e['name'],
                              command=lambda self=self, i=len(self.customMenuCommands):
                              self.doCommand(i))
                self.customMenuCommands.append((e['file'], e['gisearch'], e['psearch'], e['reset']))

    def addMenu(self, menuList, menu):
        menuList.sort(self.compare)

        for item in menuList:
            m = Menu(menu)
            menu.add_cascade(label=item['name'], menu=m)
            self.addMenu(item['subm'], m)
            for e in item['entries']:
                m.add_command(label=e['name'],
                              command=lambda self=self, i=len(self.customMenuCommands):
                              self.doCommand(i))
                self.customMenuCommands.append((e['file'], e['gisearch'], e['psearch'], e['reset']))

    def removeMenus(self):
        for i in range(self.noOfMenus):
            self.mainMenu.delete(3)  # The first custom menu is the 3rd overall menu

    def doCommand(self, i):
        if self.customMenuCommands[i][0]:
            try:
                webbrowser.open(self.customMenuCommands[i][0], new=1)
            except:
                showwarning(_('Error'), _('Failed to open the web browser.'))
        if self.customMenuCommands[i][3]:   # reset game list
            self.master.reset()
        if self.customMenuCommands[i][2]:   # prepare pattern search
            self.displayPattern(self.customMenuCommands[i][2])
        if self.customMenuCommands[i][1]:   # do game info search
            self.displayGI(self.customMenuCommands[i][1])
            self.master.doGISearch()
        if self.customMenuCommands[i][2]:   # do pattern search
            self.master.search()

    def displayPattern(self, data):
        if not data:
            return
        if self.master.dataWindow.filelist.list.curselection():
            index = int(self.master.dataWindow.filelist.list.curselection()[0])
            if self.master.filelist[index][1]:
                self.master.newFile()
        else:
            self.master.newFile()

        self.master.start()

        sel = data[0]
        if sel == ((0, 0), (18, 18)):  # TODO boardsize
            self.master.board.delete('selection')
            self.master.board.selection = sel
        else:
            self.master.board.setSelection(sel[0], sel[1])

        self.master.board.changed.set(1)

        self.master.fixedAnchorVar.set(data[2])
        self.master.fixedColorVar.set(data[3])
        self.master.moveLimit.set(data[4])
        self.master.nextMoveVar.set(data[5])

        d = data[1]
        for ii in range(sel[0][1], sel[1][1] + 1):
            for jj in range(sel[0][0], sel[1][0] + 1):
                if d[(ii - 1, jj - 1)] == 'X':
                    nM = 'AB'
                elif d[(ii - 1, jj - 1)] == 'O':
                    nM = 'AW'
                elif d[(ii - 1, jj - 1)] in ['x', 'o', '*']:
                    wc_type = d[(ii - 1, jj - 1)]
                    x1, x2, y1, y2 = self.master.board.getPixelCoord((jj, ii), 1)
                    self.master.board.wildcards[(jj, ii)] = (self.master.board.create_oval(x1 + 4, x2 + 4, y1 - 4, y2 - 4,
                                                                                          fill={'*': 'green', 'x': 'black', 'o': 'white'}[wc_type],
                                                                                          tags=('wildcard', 'non-bg')),
                                                             wc_type)
                    continue
                else:
                    continue

                pos = chr(jj + ord('a')) + chr(ii + ord('a'))

                try:
                    if ('AB' in self.master.cursor.currentNode() or 'AW' in self.master.cursor.currentNode()
                       or 'AE' in self.master.cursor.currentNode()):
                        if not nM in self.master.cursor.currentNode():
                            self.master.cursor.currentNode()[nM] = []

                        if not pos in self.master.cursor.currentNode()[nM]:
                            self.master.cursor.currentNode().add_property_value(nM, [pos, ])

                        color = 'black' if nM == 'AB' else 'white'

                        if not self.master.board.play((jj, ii), color):
                            self.master.board.undostack_append_pass()
                        self.master.board.currentColor = self.master.modeVar.get()

                        if nM == 'AB':
                            self.master.capB = self.master.capB + len(self.master.board.undostack_top_captures())
                        if nM == 'AW':
                            self.master.capW = self.master.capW + len(self.master.board.undostack_top_captures())
                        self.master.capVar.set('Cap - B: %d, W: %d' % (self.master.capB, self.master.capW))

                    else:
                        s = ';' + nM + '[' + pos + ']'
                        self.master.cursor.add(s)
                        c = self.master.cursor.currentNode()

                        self.master.board.delMarks()
                        self.master.board.delLabels()

                        self.master.moveno.set(str(int(self.master.moveno.get()) + 1))

                        self.master.displayNode(c)

                        if nM == 'AB':
                            self.master.capB = self.master.capB + len(self.master.board.undostack_top_captures())
                        if nM == 'AW':
                            self.master.capW = self.master.capW + len(self.master.board.undostack_top_captures())
                        self.master.capVar.set('Cap - B: %d, W: %d' % (self.master.capB, self.master.capW))
                except SGFError:
                    showwarning(_('Error'), _('SGF Error'))

        self.master.board.currentColor = self.master.modeVar.get()[:5]

    def c_buildList(self, menuList, level):
        for i in range(len(menuList)):
            item = menuList[i]
            self.list.insert('end', '-' * level + ' ' + item['name'])
            self.correspEntry.append([1, item, '-' * level + ' ', menuList, i])                  # 1 = submenu
            self.c_buildList(item['subm'], level + 1)
            for j in range(len(item['entries'])):
                entry = item['entries'][j]
                self.list.insert('end', '-' * level + '* ' + entry['name'])
                self.correspEntry.append([2, entry, '-' * level + '* ', item['entries'], j])             # 2 = entry

    def count(self, i):
        res = len(i['entries']) + 1
        for j in i['subm']:
            res += self.count(j)
        return res

    def displayGI(self, data):
        if not data:
            return
        varList = [self.master.pwVar, self.master.pbVar, self.master.pVar,
                   self.master.evVar, self.master.frVar, self.master.toVar,
                   self.master.awVar, self.master.referencedVar]

        for i in range(len(varList)):
            varList[i].set(data[i])

    def c_addEntry(self):
        if not self.current:
            return
        index = int(self.current[0])
        if self.correspEntry[index][0] != 1:
            return

        # add entry to currently selected submenu, named 'New'

        entry = {'name': _('New'), 'file': '', 'gisearch': (), 'psearch': (), 'reset': 1}
        self.correspEntry[index][1]['entries'].append(entry)

        insertIndex = index + self.count(self.correspEntry[index][1]) - 1

        self.correspEntry[insertIndex:insertIndex] = [[2, entry, self.correspEntry[index][2][:-1] + '* ',
                                               self.correspEntry[index][1]['entries'],
                                               len(self.correspEntry[index][1]['entries']) - 1]]

        self.list.insert(insertIndex, self.correspEntry[index][2][:-1] + '* ' + _('New'))
        self.list.list.select_clear(self.list.list.curselection())
        self.list.list.select_set(insertIndex)

    def c_addSubmenu(self):
        if not self.current:
            return
        index = int(self.current[0])
        if self.correspEntry[index][0] == 2:
            return

        # add submenu to currently selected submenu, named 'New'

        submenu = {'name': _('New'), 'entries': [], 'subm': []}

        if self.correspEntry[index][0] == 0:
            self.customMenuList.append(submenu)
            insertIndex = self.list.list.index('end')
            prefix = '- '
            self.correspEntry.append([1, submenu, prefix, self.customMenuList, len(self.customMenuList) - 1])
        else:
            self.correspEntry[index][1]['subm'].append(submenu)

            insertIndex = index + self.count(self.correspEntry[index][1]) - len(self.correspEntry[index][1]['entries']) - 1

            prefix = self.correspEntry[index][2][:-1] + '- '

            self.correspEntry[insertIndex:insertIndex] = [[1, submenu, prefix,
                                                           self.correspEntry[index][1]['subm'],
                                                           len(self.correspEntry[index][1]['subm']) - 1]]

        self.list.insert(insertIndex, prefix + _('New'))
        self.list.list.select_clear(self.list.list.curselection())
        self.list.list.select_set(insertIndex)

    def c_delete(self):

        if not self.current:
            return
        index = int(self.current[0])
        if self.correspEntry[index][0] == 0:
            return

        if self.correspEntry[index][0] == 1:
            n = self.count(self.correspEntry[index][1])
        elif self.correspEntry[index][0] == 2:
            n = 1

        del self.correspEntry[index][3][self.correspEntry[index][4]]
        del self.correspEntry[index:index + n]

        self.correspEntry = [[0, '', '', None, None]]
        self.list.delete(1, 'end')
        self.c_buildList(self.customMenuList, 1)

        if self.list.list.index('end') > index:
            self.list.list.select_set(index)
        else:
            self.list.list.select_set('end')
        self.current = None

    def c_addPattern(self):
        if not self.current:
            return
        index = int(self.current[0])
        if self.correspEntry[index][0] != 2:
            return

        d = {}

        if self.master.board.selection[0][0] > self.master.board.selection[1][0] or self.master.board.selection[0][1] > self.master.board.selection[1][1]:
            self.master.board.selection = ((1, 1), (19, 19))  # TODO boardsize

        sel = self.master.board.selection  # copy this because the selection on the board may
                                           # be changed by the user although the search is not yet
                                           # finished

        for i in range(sel[0][1], sel[1][1] + 1):
            for j in range(sel[0][0], sel[1][0] + 1):
                if self.master.board.getStatus(j, i) == 'W':
                    d[(i - 1, j - 1)] = 'O'
                elif self.master.board.getStatus(j, i) == 'B':
                    d[(i - 1, j - 1)] = 'X'
                else:
                    d[(i - 1, j - 1)] = '.'
                if (j, i) in self.master.board.wildcards:
                    d[(i - 1, j - 1)] = self.master.board.wildcards[(j,i)][1]

        self.correspEntry[index][1]['psearch'] = (sel, d,
                                                  self.master.fixedAnchorVar.get(),
                                                  self.master.fixedColorVar.get(),
                                                  self.master.moveLimit.get(),
                                                  self.master.nextMoveVar.get())

        showinfo(_('Add pattern'), _('Successfully stored pattern.'))
        self.window.lift()

    def c_addGI(self):
        if not self.current:
            return
        index = int(self.current[0])
        if self.correspEntry[index][0] != 2:
            return

        self.correspEntry[index][1]['gisearch'] = (self.master.pwVar.get(), self.master.pbVar.get(), self.master.pVar.get(),
                                                   self.master.evVar.get(), self.master.frVar.get(), self.master.toVar.get(),
                                                   self.master.awVar.get(), self.master.referencedVar.get())

        showinfo(_('Add game info'), _('Successfully stored game info.'))
        self.window.lift()

    def c_OK(self):
        if self.current:
            index = int(self.current[0])
            if self.correspEntry[index][0] == 1:
                entry = self.correspEntry[index][1]
                entry['name'] = self.nameCurrent.get()

            if self.correspEntry[index][0] == 2:
                entry = self.correspEntry[index][1]
                entry['name'] = self.nameCurrent.get()
                entry['file'] = self.htmlCurrent.get()
                entry['reset'] = self.resetVar.get()
        self.removeMenus()
        self.buildMenus(0)

        # save menus ...

        try:
            file = open(os.path.join(self.path, 'menus.def'), 'wb')
            cPickle.dump(self.customMenuList, file)
            file.close()
        except IOError:
            showwarning(_('I/O Error'), _('Could not save custom menu file.'))

        self.window.destroy()

    def c_cancel(self):
        self.removeMenus()
        self.buildMenus()
        self.window.destroy()

    def c_setName(self, event=None):
        index = int(self.current[0])
        self.list.delete(index)
        self.correspEntry[index][1]['name'] = self.nameCurrent.get()
        self.list.insert(index, self.correspEntry[index][2] + self.correspEntry[index][1]['name'])
        # self.htmlE.focus()
        # self.list.list.select_set(index)

    def c_browse(self, event=None):
        if not self.current:
            return
        index = int(self.current[0])
        if self.correspEntry[index][0] != 2:
            return

        filename = tkFileDialog.askopenfilename(filetypes=[(_('HTML files'), ('*.html', '*.htm')), (_('All files'), '*')],
                                                initialdir=self.htmlpath)

        self.window.tkraise()

        if filename:
            filename = os.path.normpath(filename)
            self.htmlpath = os.path.split(filename)[0]
            self.correspEntry[index][1]['file'] = filename
            self.htmlCurrent.set(filename)

    def pollList(self):
        now = self.list.list.curselection()
        if not now and self.current:
            self.list.list.select_set(self.current)
        elif now != self.current:
            if self.current:
                index = int(self.current[0])
                if self.correspEntry[index][0] == 1:
                    entry = self.correspEntry[index][1]
                    self.c_setName(None)
                    self.list.list.select_set(now)
                    entry['name'] = self.nameCurrent.get()
                if self.correspEntry[index][0] == 2:
                    entry = self.correspEntry[index][1]
                    self.c_setName(None)
                    self.list.list.select_set(now)
                    entry['file'] = self.htmlCurrent.get()
                    entry['reset'] = self.resetVar.get()

            self.nameCurrent.set('')
            self.htmlCurrent.set('')
            self.resetVar.set(0)
            for widget in [self.addEntryB, self.addSubmenuB, self.deleteB,
                           self.nameE, self.htmlE, self.browseB,
                           self.patternB, self.giB, self.resetB]:
                widget.config(state=DISABLED)
            self.nameE.config(takefocus=0)
            self.htmlE.config(takefocus=0)

            if now:
                self.list.list.see(now)
                index = int(now[0])
                if self.correspEntry[index][0] == 0:
                    for widget in [self.addSubmenuB]:
                        widget.config(state=NORMAL)
                elif self.correspEntry[index][0] == 1:
                    for widget in [self.addEntryB, self.addSubmenuB, self.deleteB, self.nameE]:
                        widget.config(state=NORMAL)
                    self.nameE.config(takefocus=1)
                    self.nameCurrent.set(self.correspEntry[index][1]['name'])
                elif self.correspEntry[index][0] == 2:
                    for widget in [self.deleteB, self.nameE, self.htmlE, self.browseB,
                                   self.patternB, self.giB, self.resetB]:
                        widget.config(state=NORMAL)

                    self.nameE.config(takefocus=1)
                    self.htmlE.config(takefocus=1)

                    self.nameCurrent.set(self.correspEntry[index][1]['name'])
                    self.htmlCurrent.set(self.correspEntry[index][1]['file'])
                    self.resetVar.set(self.correspEntry[index][1]['reset'])

                    self.displayPattern(self.correspEntry[index][1]['psearch'])
                    self.displayGI(self.correspEntry[index][1]['gisearch'])

            self.current = now

        self.window.after(250, self.pollList)

    def change(self):
        if self.windowOpen:
            return
        else:
            self.windowOpen = 1

        self.window = Toplevel()
        self.window.title(_('Change custom menus'))
        self.window.protocol('WM_DELETE_WINDOW', self.c_cancel)

        # scrolled list with all submenus, entries

        self.list = v.ScrolledList(self.window, width=35, font='Courier')
        self.list.pack()
        self.current = None

        self.correspEntry = [[0, '', '', None, None]]
        self.list.insert('end', '*')
        self.c_buildList(self.customMenuList, 1)

        # buttons ... for currently selected entry

        f = Frame(self.window)
        self.addEntryB = Button(f, text=_('Add entry'), command=self.c_addEntry)
        self.addSubmenuB = Button(f, text=_('Add submenu'), command=self.c_addSubmenu)
        self.deleteB = Button(f, text=_('Delete'), command=self.c_delete)
        self.addEntryB.pack(side=LEFT, anchor=W)
        self.addSubmenuB.pack(side=LEFT, anchor=W)
        self.deleteB.pack(side=LEFT, anchor=W)
        f.pack(anchor=W)

        Frame(self.window, background='black', height=1, width=100).pack(expand=YES, fill=X, pady=10)

        Label(self.window, text=_('Name:')).pack(anchor=W)

        self.nameCurrent = StringVar()
        self.nameE = Entry(self.window, width=40, textvariable=self.nameCurrent, takefocus=1)
        self.nameE.bind('<Return>', self.c_setName)
        self.nameE.bind('<Tab>', self.c_setName)
        self.nameE.pack(anchor=W)

        Frame(self.window, height=15, width=200).pack()

        Label(self.window, text=_('HTML file:')).pack(anchor=W)

        f = Frame(self.window)
        f.pack(anchor=W)
        self.htmlCurrent = StringVar()
        self.htmlE = Entry(f, width=35, textvariable=self.htmlCurrent, takefocus=1)
        self.htmlE.pack(side=LEFT)

        self.browseB = Button(f, text=_('Browse ...'), command=self.c_browse, height=1)
        self.browseB.pack(side=RIGHT)

        Frame(self.window, height=15, width=200).pack()

        f = Frame(self.window)
        self.patternB = Button(f, text=_('Add pattern info'), command=self.c_addPattern)
        self.patternB.pack(side=LEFT)
        self.giB = Button(f, text=_('Add game info'), command=self.c_addGI)
        self.giB.pack(side=LEFT)

        self.resetVar = IntVar()
        self.resetB = Checkbutton(f, text=_('Reset game list'), highlightthickness=0,
                                  variable=self.resetVar)
        self.resetB.pack(side=LEFT)
        f.pack(anchor=W)

        # OK, cancel buttons

        Frame(self.window, background='black', height=1, width=100).pack(expand=YES, fill=X, pady=10)

        f = Frame(self.window)
        f.pack(side=BOTTOM, anchor=E)
        Button(f, text=_('Cancel'), command=self.c_cancel).pack(side=RIGHT, anchor=E)
        Button(f, text=_('OK'), command=self.c_OK).pack(side=RIGHT, anchor=E)

        self.list.list.select_set(0)
        self.pollList()

        self.window.update_idletasks()
        self.window.focus()
        # self.window.grab_set()
        self.window.wait_window()

        del self.window
        self.windowOpen = 0
