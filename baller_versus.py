import pandas as pd
from nba_py import player
import sys
import re
from bs4 import BeautifulSoup
import requests

name = ""
player_id = ""
field_goals = []
field_goal_pcts = []
mid_range = 0
three_point = 0
free_throw = 0
steals = 0
blocks = 0
assists = 0

d_rpm_score = 0
steals_and_blocks_score = 0
assist_score = 0
solo_score = 0
dunks_score = 0
height_score = 0

long_range = 0
inside = 0
defense = 0
playmaking = 0
athletic = 0
total = 0

years = ["2000-01", "2001-02", "2002-03", "2003-04", "2004-05", "2005-06", "2006-07", "2007-08", "2008-09", "2009-10", "2010-11", "2011-12", "2012-13", "2013-14", "2014-15", "2015-16", "2016-17"]
def get_id(first_name, last_name):
    global player_id
    player_id =  player.get_player(first_name, last_name)


def get_espn_url(page):
    # Taken from espn Defensive Real Plus-Minus
    espn_url = "http://www.espn.com/nba/statistics/rpm/_/year/2017/page/{}/sort/DRPM".format(page)

    response = requests.get(espn_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36'})
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_stats_url(year):
    stats_url = "https://stats.nba.com/draft/combine-strength-agility/#!?SeasonYear={}".format(years[year])
    response = requests.get(stats_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36'})
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_defense_rpm(page):
    if page > 12:
        return 0
    soup = get_espn_url(page)
    content = soup.findAll('div', attrs={'class': 'mod-content'})[1]
    table = content.find('table', attrs={'class': 'tablehead'})
    rows = table.findAll('tr')
    for row in rows[1:]:
        data = row.findAll('td')[1]
        for link in data.find('a'):
            if link.string.lower() == name:
                d_rpm = row.findAll('td')[6].text
                return d_rpm
    page+=1
    return get_defense_rpm(page)


def get_vertical_leap(year):
    if year >= 17:
        return 0
    soup = get_stats_url(year)
    stats = soup.find('div', attrs={'class': 'stats-draft-page'})
    overlay = stats.find('div', attrs={'class': 'columns / small-12 / section-view-overlay'})
    stat_table = overlay.find('nba-stat-table')
    return stat_table
    div = stat_table.find('div')
    return div 
    table = stat_table.find('div', attrs={'class': 'nba-stat-table'})
    return table
    rows = table.findAll('tr')
    for row in rows:
        row_name = row.find('td', attrs={'class': 'first'}).text
        if row_name == name:
            vertical = row.findAll('td')[6].text
            return vertical
    year+=1
    return get_vertical_leap(year)


   

def get_passing_stats():
    my_player = player.PlayerPassTracking(player_id)
    assists = my_player.passes_made()
    twos_assist = assists["FG2M"]
    threes_assist = assists["FG3M"]
    points_created = get_points_created_impact(twos_assist, threes_assist)
    return points_created

def get_player_info(key):
    my_player = player.PlayerSummary(player_id)
    info = my_player.info()
    stat = info[key]
    return stat.item()

def get_player_stats():
    my_player = player.PlayerShootingSplits(player_id)
    stats = my_player.shot_5ft()
    ## LONG RANGE, MID RANGE, CLOSE RANGE AND FREE THROW SHOOTING ##
    global field_goals, field_goal_pcts
    field_goals = stats["FGM"]
    field_goal_pcts = stats["FG_PCT"]
    get_2pt_impact(field_goals, field_goal_pcts)
    get_3pt_impact_and_free_throw()
    
    ## DUNKS ##
    shot_types = my_player.shot_types_summary()
    shots_made = shot_types["FGM"]
    dunks = shots_made[2]
    
    ## HEIGHT ##
    height_info = get_player_info("HEIGHT")
    height = get_inches_calc(height_info)
    
    ## ATHLETICISM ##
    get_athletic_impact(height, dunks)
    
    ## SHOTS ASSISTED BY AND TO ##
    assisted_stats = my_player.assisted_shots()
    two_shots_made = assisted_stats["FGM"]
    three_shots_made = assisted_stats["FG3M"]
    solo_points = get_unassisted_impact(two_shots_made, three_shots_made)
    points_created = get_passing_stats()
    get_playmaking_impact(points_created, solo_points)
    #return get_vertical_leap(1)
    #return stats
    
    ## DEFENSE ##
    get_defense_impact()
    #return two_pt_stats + three_pt_and_free_stats
    global total
    total = long_range + inside + defense + athletic + playmaking


def get_3pt_impact_and_free_throw():
    global free_throw, three_point, blocks, steals, long_range
    my_player = player.PlayerGeneralSplits(player_id)
    career_stats = my_player.overall()
    three_pointers_made = career_stats["FG3M"]
    three_pointers_att = career_stats["FG3A"]
    blocks = career_stats['BLK'].item()
    steals = career_stats['STL'].item()
    three_point_score_series = ((three_pointers_made/three_pointers_att) * three_pointers_made)

    free_throw_pct_series = career_stats["FT_PCT"]
    free_throw_pct = free_throw_pct_series.item()

    three_point_score = three_point_score_series.item()
    free_throw = get_free_throw_score(free_throw_pct)
    three_point = get_3pt_score(three_point_score)
    long_range = mid_range + three_point + free_throw

def get_2pt_impact(fgs, pcts):
    global mid_range, inside
    less_than_five = field_goal_pcts[0] * 2 * field_goals[0]
    five_to_nine = field_goal_pcts[1] * 2 * field_goals[1]
    ten_to_fourteen = field_goal_pcts[2]*2 * field_goals[2]
    fifteen_to_nineteen = field_goal_pcts[3]* 2 * field_goals[3] 
    
    two_point_score = (ten_to_fourteen+fifteen_to_nineteen)/2
    inside_score = (less_than_five+five_to_nine)/2
    
    mid_range = get_mid_range_score(two_point_score)
    inside = get_inside_score(inside_score)

    

def get_defense_impact():
    global defense, d_rpm_score, steals_and_blocks_score
    d_rpm = float(get_defense_rpm(1))
    d_rpm_score = get_drpm_score(d_rpm)
    steals_and_blocks_score = get_steals_blocks_score(steals + blocks)
    defense = d_rpm_score + steals_and_blocks_score

    #my_player = player.PlayerShotTracking(player_id)                                                                                                                                                       
    #defending_stats = my_player.closest_defender_shooting()                                                                                                                                                
    #twos_atts = defending_stats["FG2A"]                                                                                                                                                                    
    #twos_pcts = defending_stats["FG2_PCT"]                                                                                                                                                                 
    #threes_atts = defending_stats["FG3A"]                                                                                                                                                                  
    #threes_pcts = defending_stats["FG3_PCT"]                                                                                                                                                              

    #very_tight_range = defense_impact_calc(twos_atts[0], twos_pcts[0], threes_atts[0], threes_pcts[0])                                                                                                     
    #tight_range = defense_impact_calc(twos_atts[1], twos_pcts[1], threes_atts[1], threes_pcts[1])                                                                                                          
    #open_range = defense_impact_calc(twos_atts[2], twos_pcts[2], threes_atts[2], threes_pcts[2])                                                                                                           

    #defense = very_tight_range + tight_range + open_range                                                                                                                                                  
    #points allowed per game           

def get_playmaking_impact(assist, solo):
    global playmaking, assist_score, solo_score
    if assist >= 24:
        assist_score = 6
    elif assist >= 20:
        assist_score = 5
    elif assist >= 15:
        assist_score = 4
    elif assist >= 10:
        assist_score = 3
    elif assist >= 7:
        assist_score = 2
    elif assist >= 5:
        assist_score = 1
    else:
        assist_score = 0


   
    if solo >= .5:
        solo_score = 4
    elif solo >= .4:
        solo_score = 3
    elif solo >= .3:
        solo_score = 2
    elif solo >= .2:
        solo_score = 1
    else:
        solo_score = 0

    playmaking = assist_score + solo_score

def get_athletic_impact(height, dunks):
    global athletic, dunks_score, height_score
    score = 0
    if height >= 83:
        height_score = 1
    elif height >= 79:
        height_score = 2
    elif height >= 76:
        height_score = 3
    else:
        height_score = 4

    if dunks >= 140:
        dunks_score = 10
    elif dunks >= 70:
        dunks_score = 7
    elif dunks >= 35:
        dunks_score = 5
    elif dunks >= 15:
        dunks_score = 4
    elif dunks >= 5:
        dunks_score = 3
    else:
        dunks_score = 1 # EVERY PLAYER SHOULD BE ABLE TO DUNK!

    athletic = min(10, dunks_score + height_score)
    
def get_points_created_impact(twos, threes):
    points = 0
    for two in twos:
        points += two*2
    for three in threes:
        points += three*3
    return points



def get_unassisted_impact(twos, threes):
    twos_assisted = twos[0] * 2
    twos_unassisted = twos[1] * 2
    threes_assisted = threes[0] * 3
    threes_unassisted = threes[1] * 3
    
    score = (float(twos_unassisted + threes_unassisted))/ (twos_unassisted + threes_unassisted + twos_assisted + threes_assisted)
    return score

def get_free_throw_score(ft_pct):
    if ft_pct >= 0.87:
        return 3
    elif ft_pct >= 0.80:
        return 2
    elif ft_pct >= 0.50:
        return 1
    else:
        return 0

def get_3pt_score(three_point):
    if pd.isnull(three_point):
        return 0

    if three_point >= 1.3:
        return 5
    elif three_point >= 0.8:
        return 4
    elif three_point >= 0.7:
        return 3
    elif three_point >= 0.5:
        return 2
    elif three_point >= 0.3:
        return 1
    else:
        return 0

    
def get_drpm_score(d_rpm):
    if d_rpm >= 5:
        return 8
    elif d_rpm >= 4:
        return 7
    elif d_rpm >= 3:
        return 6
    elif d_rpm >= 2:
        return 5
    elif d_rpm >= 1:
        return 4
    elif d_rpm >= 0:
        return 3
    elif d_rpm >= -1:
        return 2
    elif d_rpm >= -2:
        return 1
    else:
        return 0

def get_steals_blocks_score(total):
    if total >= 2:
        return 2
    elif total >= 1:
        return 1
    else:
        return 0
    
def get_mid_range_score(mid):
    if mid >= 70:
        return 2
    elif mid >= 20:
        return 1
    else:
        return 0

def get_inside_score(inside):
    if inside >= 300:
        return 10
    elif inside >= 250:
        return 9
    elif inside >= 200:
        return 8
    elif inside >= 175:
        return 7
    elif inside >= 150:
        return 6
    elif inside >= 125:
        return 5
    elif inside >= 100:
        return 4
    elif inside >= 75:
        return 3
    elif inside >= 50:
        return 2
    elif inside >= 25:
        return 1
    else:
        return 0

def defense_impact_calc(twos_att, two_pct, threes_att, three_pct):
    if pd.isnull(three_pct):
        three_pct = 0
    if pd.isnull(two_pct):
        two_pct = 0
    two_points_allowed = two_pct * twos_att * 2
    three_points_allowed = three_pct * threes_att * 3
    return two_points_allowed + three_points_allowed

def get_inches_calc(height):
    r = re.compile(r"([0-9]+)-([0-9]*\.?[0-9]+)")
    m = r.match(height)
    return int(m.group(1))*12 + int(m.group(2))

if __name__ == '__main__':
    first_name, last_name = sys.argv[1], sys.argv[2]
    name = first_name + " " + last_name
    get_id(first_name, last_name)
    stats = get_player_stats()
    divider = "------------"
    print "\nBallerVersus for {} {}:\n\nLong Range Shooting: {} out of 10.\n{}\nThree Point Impact: {} out of 5\nMid_Range Impact: {} out of 2.\nFree Throw Score: {} out of 3.\n\nInside Shooting: {} out of 10.\n{}\n\nDefense: {} out of 10.\n{}\nDRPM Score: {} out of 8.\nSteals and Blocks Score: {} out of 2.\n\nPlaymaking: {} out of 10.\n{}\nUnassisted Scoring Impact: {} out of 4.\nPoints Created by Assists Score: {} out of 6\n\nAthleticism: {} out of 10.\n{}\nHeight Score: {} out of 4.\nDunk Score: {} out of 10.\n\nTotal of {} out of 50\n".format(first_name, last_name, long_range, divider, three_point, mid_range, free_throw, inside, divider, defense, divider, d_rpm_score, steals_and_blocks_score, playmaking, divider, solo_score, assist_score, athletic, divider, height_score, dunks_score, total)




