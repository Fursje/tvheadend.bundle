NAME = 'TVHeadend'
#ART = 'art-default.jpg'
ICON = 'icon-default.png'
PLUGIN_PREFIX = '/video/tvheadend'

#import
import urllib2, base64, simplejson, time
json = simplejson

#Prefs
username = '%s' % (Prefs['tvheadend_user']) 
password = '%s' % (Prefs['tvheadend_pass'])
hostname = '%s' % (Prefs['tvheadend_host'])
web_port = '%s' % (Prefs['tvheadend_web_port'])
htsp_port = '%s' % (Prefs['tvheadend_htsp_port'])
options_transcode = '%s' % (Prefs['tvheadend_transcode'])

#Links Structures
structure = 'stream/channelid'
transcode = '?mux=mpegts&acodec=aac&vcodec=H264&transcode=1&resolution=384' ## Proof Of Concept
htsurl = 'http://%s:%s@%s:%s/%s/' % (username, password, hostname, web_port, structure)

#Texts
TEXT_TITLE = u'HTS-TVheadend'
TEXT_CHANNELS = u'All Channels'
TEXT_TAGS = u'Tags'
TEXT_EPG = u'EPG'
TEXT_PREFERENCES = u'Settings'

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, NAME, ICON)

#	ObjectContainer.art = R(ART)	
	TrackObject.thumb = R(ICON)

####################################################################################################

@handler('/video/tvheadend', TEXT_TITLE, thumb=ICON)
def MainMenu():

	menu = ObjectContainer(title1=TEXT_TITLE)
	menu.add(DirectoryObject(key=Callback(GetChannels, prevTitle=TEXT_TITLE), title=TEXT_CHANNELS, thumb=R('channel.png')))
	menu.add(DirectoryObject(key=Callback(GetbyTags, prevTitle=TEXT_TITLE), title=TEXT_TAGS, thumb=R('tag.png')))
	menu.add(DirectoryObject(key=Callback(GetbyTags, prevTitle=TEXT_TITLE, epgMenu=True), title=TEXT_EPG, thumb=R('tag.png')))
	menu.add(PrefsObject(title=TEXT_PREFERENCES, thumb=R('settings.png')))

	return menu

def getTVHeadendJson(what, url = False):
	tvh_url = dict( channels='op=list', channeltags='op=listTags', epg='start=0&limit=300')
	if url != False: 
		tvh_url[what] = url
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request = urllib2.Request("http://%s:%s/%s" % (hostname,web_port,what),tvh_url[what])
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request)
        json_tmp = response.read()
        json_data = json.loads(json_tmp)
        return json_data

def GetbyTags(prevTitle, epgMenu=False):
	json_data = getTVHeadendJson('channeltags')
	tagList = ObjectContainer(title1=prevTitle, title2=TEXT_TAGS,)

	for tag in json_data['entries']:
		if (epgMenu == False):
			tagList.add(DirectoryObject(key=Callback(GetChannels, prevTitle=tag['name'], tag=int(tag['identifier'])), title=tag['name'], thumb=R('tag.png')))
		else:
			tagList.add(DirectoryObject(key=Callback(GetChannels, prevTitle=tag['name'], tag=int(tag['identifier']), epgMenu=True), title=tag['name'], thumb=R('tag.png')))
		
	return tagList
def GetChannelEPG(prevTitle,epg_channel):
	json_data = getTVHeadendJson('epg',url='start=0&limit=100&channel=%s' % epg_channel)
	epgItems = ObjectContainer(title1=prevTitle, title2='EPG',)
	#MenuList = PopupDirectoryObject(title='test', summary='test summ')

	for epg in json_data['entries']:
		duration = 0
		epg_start = 0
		epg_end = 0
		epg_summary = ''
		epg_title = ''	
	        if 'duration' in epg:
     			duration = epg['duration']*1000
     		if 'start' in epg:
        		epg_start = time.strftime("%H:%M", time.localtime(int(epg['start'])))
     		if 'end' in epg:
       			epg_end = time.strftime("%H:%M", time.localtime(int(epg['end'])))
    		if 'description' in epg:
    			epg_summary = epg['description']
   		if 'title' in epg:
   			epg_title = "%s %s" % (epg_start, epg['title'])
			epg_summary = '%s (%s-%s)\n\n%s' % (epg['title'],epg_start,epg_end, epg_summary)
		if epg_title != '':
			epgItems.add(DirectoryObject(key=Callback(GetChannels, prevTitle=epg_channel), title=epg_title, summary=epg_summary, thumb=R('tag.png')))
		
	return epgItems


def GetChannels(prevTitle, tag=int(0), epgMenu=False):
	json_data = getTVHeadendJson('channels')
	json_data_epg = getTVHeadendJson('epg')
	channelList = ObjectContainer(title1=prevTitle, title2=TEXT_CHANNELS,)

	for channel in json_data['entries']:
		name = ''
		id = 0
		duration = 0
		summary = ''
		epg_start = 0
		epg_end = 0
		if tag > 0:
			tags = channel['tags'].split(',')
			for tids in tags:
				if (tag == int(tids)):
					name = channel['name']
					id = channel['chid']
					if 'ch_icon' in channel:
						icons = channel['ch_icon']
					else:
						icons = R('channel.png')

		else:
			name = channel['name']
			id = channel['chid']
			if 'ch_icon' in channel:
				icons = channel['ch_icon']
			else:
				icons = R('channel.png')

		if (name != '' and epgMenu == False):
			# Add epg
			for epg in json_data_epg['entries']:
				if int(epg['channelid']) == int(id):
					if 'duration' in epg:
						duration = epg['duration']*1000
					if 'start' in epg:
						epg_start = time.strftime("%H:%M", time.localtime(int(epg['start'])))
					if 'end' in epg:
						epg_end = time.strftime("%H:%M", time.localtime(int(epg['end'])))
					if 'description' in epg:
						summary = epg['description']
					if 'title' in epg:
						name = '%s -> %s' % (name, epg['title'])
						summary = '%s (%s-%s)\n\n%s' % (epg['title'],epg_start,epg_end, summary)
					break;

			if "on" in options_transcode:
				mo = MediaObject(parts=[PartObject(key=HTTPLiveStreamURL("%s%s%s" % (htsurl, id, transcode)))])
				vco = VideoClipObject(title=name, thumb=icons, summary=summary, duration=duration, url='%s%s%s' % (htsurl, id, transcode))
			else:
				mo = MediaObject(parts=[PartObject(key=HTTPLiveStreamURL("%s%s" % (htsurl, id)))])
				vco = VideoClipObject(title=name, thumb=icons,  summary=summary, duration=duration, url='%s%s' % (htsurl, id))
			vco.add(mo)
			channelList.add(vco)
		elif (name != '' and epgMenu == True):
        		channelList.add(DirectoryObject(key=Callback(GetChannelEPG, prevTitle=TEXT_TITLE,epg_channel=channel['name']), title=channel['name'], thumb=R('channel.png')))

       	return channelList

