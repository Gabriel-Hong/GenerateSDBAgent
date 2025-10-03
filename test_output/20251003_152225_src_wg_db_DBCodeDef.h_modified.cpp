#if !defined(__DBCODEDEF_H__)
#define __DBCODEDEF_H__

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

// ¿©±â ±âÁØ Ãß°¡½Ã MxT ¹Ý¿µÇØ¾ß ÇÕ´Ï´Ù. MxT ´ã´çÀÚ¿¡°Ô ¿¬¶ô
// ¾Æ·¡ Ãß°¡, ¼öÁ¤ ¹× º¯°æ»çÇ×ÀÌ ÀÖÀ¸¸é ÀÀ¿ë±â¼ú1ÆÀ DB´ã´çÀÚ¿¡°Ô ¹Ýµå½Ã ¾Ë¸±°Í.

#define FULL_ANSI_W_82			_T("ANSI(1982)")
#define FULL_BS6399_W_1997		_T("BS6399(1997)")
#define FULL_CH_W_2002			_T("China(GB50009-2001)")
#define FULL_CH_W_2012			_T("China(GB50009-2012)")
#define FULL_CH_W_2021			_T("China(GB55001-2021)")
#define FULL_DPT_W_2007			_T("DPT.1311-50:2007")
#define FULL_EURO_W_1992		_T("Eurocode-1(1992)")
#define FULL_EURO_W_2005		_T("Eurocode-1(2005)")
#define FULL_IBC_W_2000			_T("IBC2000(ASCE7-98)")
#define FULL_IBC_W_2009			_T("IBC2009(ASCE7-05)")
#define FULL_IBC_W_2012			_T("IBC2012(ASCE7-10)")
#define FULL_IS_W_1987			_T("IS875(1987)")
#define FULL_IS_W_875_2015		_T("IS875(2015)")
#define FULL_JP_W_2004			_T("Japan(2004)")
#define FULL_JP_W_87			_T("Japan(1987)")
#define FULL_JPN_W_2000			_T("Japan(Arch.2000)")
#define FULL_KBC_W_2009			_T("KBC(2009)")
#define FULL_KBC_W_2016			_T("KBC(2016)")
#define FULL_KDS_W_2019			_T("KDS(41-10-15:2019)")
#define FULL_KDS_W_2022			_T("KDS(41-12:2022)")
#define FULL_KS_W_2000			_T("Korea(Arch.2000)")
#define FULL_KS_W_92			_T("Korea(Arch.1992)")
#define FULL_NBC_W_1995			_T("NBC(1995)")
#define FULL_NSR_W_2010			_T("NSR-10")
#define FULL_TAIWAN_W_1986		_T("Taiwan(2002)")
#define FULL_UBC_W_97			_T("UBC(1997)")
#define FULL_ASCE7_W_2016       _T("ASCE7(2016)")
#define FULL_ASCE7_W_2022       _T("ASCE7(2022)")
#define FULL_NSCP_W_2024        _T("NSCP 2024")
#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
	#define FULL_RUS_W_2016_USER	_T("¬³¬± 20.113330.2016")
#else
	#define FULL_RUS_W_2016_USER	_T("SP 20.113330.2016(User Type)")
#endif


#define SHORT_ANSI_W_82			_T("ANSI1982")
#define SHORT_BS6399_W_1997		_T("BS6399(97)")
#define SHORT_CH_W_2002			_T("CH2001")
#define SHORT_CH_W_2012			_T("CH2012")
#define SHORT_CH_W_2021			_T("CH2021")
#define SHORT_DPT_W_2007		_T("DPT.1311-50:2007")
#define SHORT_EURO_W_1992		_T("EURO1992")
#define SHORT_EURO_W_2005		_T("EURO2005")
#define SHORT_IBC_W_2000		_T("IBC2000")
#define SHORT_IBC_W_2009		_T("IBC2009")
#define SHORT_IBC_W_2012		_T("IBC2012")
#define SHORT_IS_W_1987			_T("IS875(87)")
#define SHORT_IS_W_875_2015		_T("IS875(2015)")
#define SHORT_JP_W_2004			_T("JP2004")
#define SHORT_JP_W_87			_T("JP1987")
#define SHORT_JPN_W_2000		_T("JP2000")
#define SHORT_KBC_W_2009		_T("KBC(2009)")
#define SHORT_KBC_W_2016		_T("KBC(2016)")
#define SHORT_KDS_W_2019		_T("KDS(41-10-15:2019)")
#define SHORT_KDS_W_2022		_T("KDS(41-12:2022)")
#define SHORT_KS_W_2000			_T("KS2000")
#define SHORT_KS_W_92			_T("KS1992")
#define SHORT_NBC_W_1995		_T("NBC1995")
#define SHORT_NSR_W_2010		_T("NSR-10")
#define SHORT_TAIWAN_W_1986		_T("TWN2002")
#define SHORT_UBC_W_97			_T("UBC1997")
#define SHORT_ASCE7_W_2016      _T("ASCE7(2016)")
#define SHORT_ASCE7_W_2022      _T("ASCE7(2022)")
#define SHORT_NSCP_W_2024       _T("NSCP 2024")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define SHORT_RUS_W_2016_USER	_T("¬²¬µ¬³2016")
//#else
	#define SHORT_RUS_W_2016_USER	_T("RUS2016")
//#endif

#define FULL_ATC306_E			_T("ATC3-06")
#define FULL_CH_E_2001			_T("China(GB50011-2001)")
#define FULL_CH_E_2010			_T("China(GB/T50011-2010)")
#define FULL_CHSH_E_2003		_T("China Shanghai(DGJ08-9-2003)")
#define FULL_DPT_E_2018			_T("DPT.1301/1302-61:2018")
#define FULL_EURO_E_1996		_T("Eurocode-8(1996)")
#define FULL_EURO_E_2004		_T("Eurocode-8(2004)")
#define FULL_IBC_E_2000			_T("IBC2000(ASCE7-98)")
#define FULL_IBC_E_2009			_T("IBC2009(ASCE7-05)")
#define FULL_IBC_E_2012			_T("IBC2012(ASCE7-10)")
#define FULL_IS_E_2002			_T("IS1893(2002)")
#define FULL_IS_E_2016			_T("IS1893(2016)")
#define FULL_JIS_E_YY			_T("Japan(Arch.2000)")
#define FULL_KBC_E_2005			_T("KBC2005")
#define FULL_KBC_E_2009			_T("KBC(2009)")
#define FULL_KBC_E_2016			_T("KBC(2016)")
#define FULL_KDS_E_2019			_T("KDS(41-17-00:2019)")
#define FULL_KDS_E_2018			_T("KDS(17-10-00:2018)")
#define FULL_KS_E_1992			_T("Korea(Arch.1992)")
#define FULL_KS_E_2000			_T("Korea(Arch.2000)")
#define FULL_NBC_E_1995			_T("NBC(1995)")
#define FULL_NSR_E_2010			_T("NSR-10")
#define FULL_NTC_E_2008			_T("NTC2008")
#define FULL_NTC_E_2012			_T("NTC2012")
#define FULL_NTC_E_2017			_T("NTC2018")
#define FULL_P100_E_2013		_T("P100-1(2013)")
#define FULL_TAIWAN_E_1999		_T("Taiwan(1999)")
#define FULL_TAIWAN_E_2006		_T("Taiwan(2006)")
#define FULL_TAIWAN_E_2011		_T("Taiwan(2011)")
#define FULL_TAIWAN_E_2022		_T("Taiwan(2022)")
#define FULL_UBC_E_1991			_T("UBC(1991)")
#define FULL_UBC_E_1997			_T("UBC(1997)")
#define FULL_USER_TYPE			_T("User Type")
#define FULL_NSCP_E_2024        _T("NSCP 2024")
#define FULL_SANS_E_2010		_T("SANS-10160-4(2010)")

#define SHORT_ATC306_E			_T("ATC306")
#define SHORT_CH_E_2001			_T("CH2001")
#define SHORT_CH_E_2010			_T("CH2010")
#define SHORT_CHSH_E_2003		_T("CHSH2003")
#define SHORT_DPT_E_2018		_T("DPT.1301/1302-61:2018")
#define SHORT_EURO_E_1996		_T("EURO1996")
#define SHORT_EURO_E_2004		_T("EURO2004")
#define SHORT_IBC_E_2000		_T("IBC2000")
#define SHORT_IBC_E_2009		_T("IBC2009")
#define SHORT_IBC_E_2012		_T("IBC2012")
#define SHORT_IS_E_2002			_T("IS2002")
#define SHORT_IS_E_2016			_T("IS1893-2016")
#define SHORT_JIS_E_YY			_T("JP2000")
#define SHORT_KBC_E_2005		_T("KBC2005")
#define SHORT_KBC_E_2009		_T("KBC2009")
#define SHORT_KBC_E_2016		_T("KBC2016")
#define SHORT_KDS_E_2019		_T("KDS(41-17-00:2019)")
#define SHORT_KDS_E_2018		_T("KDS(17-10-00:2018)")
#define SHORT_KS_E_1992			_T("KS1992")
#define SHORT_KS_E_2000			_T("KS2000")
#define SHORT_NBC_E_1995		_T("NBC1995")
#define SHORT_NSR_E_2010		_T("NSR-10")
#define SHORT_NTC_E_2008		_T("NTC2008")
#define SHORT_NTC_E_2012		_T("NTC2012")
#define SHORT_NTC_E_2017		_T("NTC2018")
#define SHORT_P100_E_2013		_T("P100-1(2013)")
#define SHORT_TAIWAN_E_1999		_T("TWN1999")
#define SHORT_TAIWAN_E_2006		_T("TWN2006")
#define SHORT_TAIWAN_E_2011		_T("TWN2011")
#define SHORT_TAIWAN_E_2022		_T("TWN2022")
#define SHORT_UBC_E_1991		_T("UBC1991")
#define SHORT_UBC_E_1997		_T("UBC1997")
#define SHORT_USER_TYPE			_T("USER TYPE")
#define SHORT_NSCP_E_2024       _T("NSCP 2024")
#define SHORT_SANS_E_2010		_T("SANS (2010)")

// DB_ST_DN.h¿¡ D_CFS_CODE_???? Á¤ÀÇ Ãß°¡(¼ø¼­ ¹Ù²Ù¸é ¾ÈµÊ)
/// [ CFS : Cold Formed Steel Design ]
#define CFSCODE_AIK_CFSD98           _T("AIK-CFSD98")
#define CFSCODE_AISI_CFSD08          _T("AISI-CFSD08")
#define CFSCODE_AISI_CFSD86          _T("AISI-CFSD86")
#define CFSCODE_EC3_06               _T("Eurocode3-1-3:06")
#define CFSCODE_GB50018_02           _T("GB50018-02")
#define CFSCODE_GB50018_25           _T("GB/T50018-25")

enum EN_MGTIDX_CFSCODE
{
#define MATLCODE_STL_SP16_2017_TB3 _T("SP16.2017t.B3(S)")
	EN_MGTIDX_CFSCODE_NONE = 0,
#define MATLCODE_STL_SP16_2017_TB4 _T("SP16.2017t.B4(S)")
	EN_MGTIDX_CFSCODE_AIK_CFSD98,
#define MATLCODE_STL_SP16_2017_TB5 _T("SP16.2017t.B5(S)")
	EN_MGTIDX_CFSCODE_AISI_CFSD86,
	EN_MGTIDX_CFSCODE_EUROCODE3_1_3_06,
	EN_MGTIDX_CFSCODE_AISI_CFSD08, 
	EN_MGTIDX_CFSCODE_GB50018_02,
	EN_MGTIDX_CFSCODE_GB50018_25,
};

// DB_ST_DT_DN.h¿¡ D_STL_CODE_???? Á¤ÀÇ Ãß°¡(¼ø¼­ ¹Ù²Ù¸é ¾ÈµÊ)
/// [ STL : Steel Design ]
#define STLCODE_AASHTO_ASD96         _T("AASHTO-ASD96")
#define STLCODE_AASHTO_LFD96         _T("AASHTO-LFD96")
#define STLCODE_AASHTO_LRFD02        _T("AASHTO-LRFD02")
#define STLCODE_AASHTO_LRFD07        _T("AASHTO-LRFD07")
#define STLCODE_AASHTO_LRFD12        _T("AASHTO-LRFD12")
#define STLCODE_AASHTO_LRFD16        _T("AASHTO-LRFD16")
#define STLCODE_AASHTO_LRFD17        _T("AASHTO-LRFD17")
#define STLCODE_AASHTO_LRFD20        _T("AASHTO-LRFD20")
#define STLCODE_AASHTO_STD2K         _T("AASHTO-Std2K")
#define STLCODE_AIJ_ASD02            _T("AIJ-ASD02")
#define STLCODE_AIK_ASD83            _T("AIK-ASD83")
#define STLCODE_AIK_CFSD98           _T("AIK-CFSD98")
#define STLCODE_AIK_LSD97            _T("AIK-LSD97")
#define STLCODE_AISC_ASD05           _T("AISC(13th)-ASD05")
#define STLCODE_AISC_ASD10           _T("AISC(14th)-ASD10")
#define STLCODE_AISC_ASD16           _T("AISC(15th)-ASD16")
#define STLCODE_AISC_ASD22           _T("AISC(16th)-ASD22")
#define STLCODE_AISC_ASD89           _T("AISC-ASD89")
#define STLCODE_AISC_LRFD05          _T("AISC(13th)-LRFD05")
#define STLCODE_AISC_LRFD10          _T("AISC(14th)-LRFD10")
#define STLCODE_AISC_LRFD16          _T("AISC(15th)-LRFD16")
#define STLCODE_AISC_LRFD22          _T("AISC(16th)-LRFD22")
#define STLCODE_AISC_LRFD2K          _T("AISC-LRFD2K")
#define STLCODE_AISC_LRFD93          _T("AISC-LRFD93")
#define STLCODE_AISI_CFSD08          _T("AISI-CFSD08")
#define STLCODE_AISI_CFSD86          _T("AISI-CFSD86")
#define STLCODE_BS5950_2K            _T("BS5950-2K")
#define STLCODE_BS5950_90            _T("BS5950-90")
#define STLCODE_CJJ77_98             _T("CJJ77-98")
#define STLCODE_CSA_S16_01           _T("CSA-S16-01")
#define STLCODE_CSA_S6_14            _T("CSA-S6-14")
#define STLCODE_CSA_S6_19            _T("CSA-S6-19")
#define STLCODE_CSA_S6S1_10          _T("CSA-S6S1-10")
#define STLCODE_EC0                  _T("Eurocode 0")
#define STLCODE_EC3                  _T("Eurocode3")
#define STLCODE_EC3_05               _T("Eurocode3:05")
#define STLCODE_EC3_2_05             _T("Eurocode3-2:05")
#define STLCODE_GB50017_03           _T("GB50017-03")
#define STLCODE_GB50017_15           _T("GB50017-15") //add by maxiao(2015-9-24)GB50017-15
#define STLCODE_GB50017_17           _T("GB50017-17") //add by xuezc(2018/2/7)
#define STLCODE_GB51249_2017		 _T("GB51249-2017")
#define STLCODE_GB55006_2021         _T("GB55006-2021") //add by tss(2022/03/10)
#define STLCODE_GBJ17_88             _T("GBJ17-88")
#define STLCODE_IRC_24_2010          _T("IRC:24-2010")
#define STLCODE_IRC_6_LSD            _T("IRC:6 LSD")
#define STLCODE_IS800_1984           _T("IS:800-1984")
#define STLCODE_IS800_2007           _T("IS:800-2007")
#define STLCODE_JGJ209_2010          _T("JGJ209-2010") //Add by tss 20210715
#define STLCODE_JROAD_H29            _T("Japan Road II-H29")   // JSCE17¿¡¼­ º¯°æ
#define STLCODE_JROAD_H24            _T("Japan Road II-H24")   // 2012³â - Æò¼º 24³â
#define STLCODE_JROAD_H14            _T("Japan Road II-H14")   // 2002³â - Æò¼º 14³â
#define STLCODE_JTG_D60_15           _T("JTG D60-15") // added by qiangeng(2019/1/16)
#define STLCODE_JTJ021_89            _T("JTJ021-89")
#define STLCODE_JTJ025_86            _T("JTJ025-86")
#define STLCODE_KBC_ASD05            _T("KBC-ASD05")
#define STLCODE_KBC_LSD09            _T("KBC-LSD09")
#define STLCODE_KBC_LSD16            _T("KBC-LSD16")
#define STLCODE_KDS_24_14_31_2018    _T("KDS 24 14 31 : 2018")
#define STLCODE_KDS_24_14_30_2019    _T("KDS 24 14 30 : 2019")
#define STLCODE_KDS_41_30_10_2022    _T("KDS 41 30 : 2022")
#define STLCODE_KDS_41_31_2019       _T("KDS 41 31 : 2019")
#define STLCODE_KEPCO97_1111         _T("KEPCO97-1111")
#define STLCODE_KSCE_ASD05           _T("KSCE-ASD05")
#define STLCODE_KSCE_ASD10           _T("KSCE-ASD10")
#define STLCODE_KSCE_ASD96           _T("KSCE-ASD96")
#define STLCODE_KSCE_LSD15           _T("KSCE-LSD15")
#define STLCODE_KSCE_RAIL_ASD04      _T("KSCE-RAIL-ASD04")
#define STLCODE_KSCE_RAIL_ASD11      _T("KSCE-RAIL-ASD11")
#define STLCODE_KSSC_ASD03           _T("KSSC-ASD03")
#define STLCODE_KSSC_LSD09           _T("KSSC-LSD09")
#define STLCODE_KSSC_LSD16           _T("KSSC-LSD16")
#define STLCODE_NSCP_2015_ASD        _T("NSCP 2015(ASD)")
#define STLCODE_NSCP_2015_LRFD       _T("NSCP 2015(LRFD)")
#define STLCODE_PN_85_S_10030        _T("PN-85/S-10030")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define STLCODE_SNIP_2_05_03_84      _T("¬³¬¯¬Ú¬± 2.05.03-84*")
//	#define STLCODE_SNIP_2_05_03_84_MKS  _T("¬³¬¯¬Ú¬± 2.05.03-84*(MKS)")
//	#define STLCODE_SP_35_13330_2011     _T("¬³¬± 35.13330.2011")
//	#define STLCODE_SP_35_13330_2011_MKS _T("¬³¬± 35.13330.2011(MKS)")
//#else
	#define STLCODE_SNIP_2_05_03_84      _T("SNiP 2.05.03-84*")
	#define STLCODE_SNIP_2_05_03_84_MKS  _T("SNiP 2.05.03-84*(MKS)")
	#define STLCODE_SP_35_13330_2011     _T("SP 35.13330.2011")
	#define STLCODE_SP_35_13330_2011_MKS _T("SP 35.13330.2011(MKS)")
//#endif
#define STLCODE_TAIWAN               _T("Taiwan")
#define STLCODE_TWN_ASD90            _T("TWN-ASD90")
#define STLCODE_TWN_ASD96            _T("TWN-ASD96")
#define STLCODE_TWN_BRG_ASD90        _T("TWN-BRG-ASD90")
#define STLCODE_TWN_BRG_LSD90        _T("TWN-BRG-LSD90")
#define STLCODE_TWN_LSD90            _T("TWN-LSD90")
#define STLCODE_TWN_LSD96            _T("TWN-LSD96")
#define STLCODE_IRS_SBC              _T("IRS SBC")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define STLCODE_SP_16_13330_2017     _T("¬³¬± 16.13330.2017")
//#else
	#define STLCODE_SP_16_13330_2017     _T("SP 16.13330.2017")
//#endif

enum EN_MGTIDX_STLCODE
{
	EN_MGTIDX_STLCODE_NONE = 0,
	EN_MGTIDX_STLCODE_AISC_ASD89,
	EN_MGTIDX_STLCODE_AISC_LRFD93,
	EN_MGTIDX_STLCODE_AISI_CFSD86,
	EN_MGTIDX_STLCODE_EC3,
	EN_MGTIDX_STLCODE_BS5950_90,
	EN_MGTIDX_STLCODE_AIK_ASD83,
	EN_MGTIDX_STLCODE_KSCE_ASD96,
	EN_MGTIDX_STLCODE_AIK_LSD97,
	EN_MGTIDX_STLCODE_AIK_CFSD98,
	EN_MGTIDX_STLCODE_AIJ_ASD02,
	EN_MGTIDX_STLCODE_KEPCO97_1111,
	EN_MGTIDX_STLCODE_AISC_LRFD2K,
	EN_MGTIDX_STLCODE_JTJ021_89,
	EN_MGTIDX_STLCODE_CJJ77_98,
	EN_MGTIDX_STLCODE_AASHTO_STD2K,
	EN_MGTIDX_STLCODE_GBJ17_88,
	EN_MGTIDX_STLCODE_AASHTO_LRFD02,
	EN_MGTIDX_STLCODE_CSA_S16_01,
	EN_MGTIDX_STLCODE_JTJ025_86,
	EN_MGTIDX_STLCODE_IS800_1984,
	EN_MGTIDX_STLCODE_TAIWAN,
	EN_MGTIDX_STLCODE_TWN_BRG_LSD90,
	EN_MGTIDX_STLCODE_AASHTO_LFD96,
	EN_MGTIDX_STLCODE_TWN_ASD90,
	EN_MGTIDX_STLCODE_TWN_LSD90,
	EN_MGTIDX_STLCODE_GB50017_03,
	EN_MGTIDX_STLCODE_TWN_BRG_ASD90,
	EN_MGTIDX_STLCODE_AASHTO_ASD96,
	EN_MGTIDX_STLCODE_KSSC_ASD03,
	EN_MGTIDX_STLCODE_BS5950_2K,
	EN_MGTIDX_STLCODE_KBC_ASD05,
	EN_MGTIDX_STLCODE_KSCE_ASD05,
	EN_MGTIDX_STLCODE_EC3_05,
	EN_MGTIDX_STLCODE_EC0,
	EN_MGTIDX_STLCODE_IS800_2007,
	EN_MGTIDX_STLCODE_AASHTO_LRFD07,
	EN_MGTIDX_STLCODE_KSSC_LSD09,
	EN_MGTIDX_STLCODE_KBC_LSD09,
	EN_MGTIDX_STLCODE_AISC_LRFD05,
	EN_MGTIDX_STLCODE_AISC_ASD05,
	EN_MGTIDX_STLCODE_TWN_ASD96,
	EN_MGTIDX_STLCODE_TWN_LSD96,
	EN_MGTIDX_STLCODE_KSCE_LSD15,
	EN_MGTIDX_STLCODE_KSCE_ASD10,
	EN_MGTIDX_STLCODE_KSCE_RAIL_ASD04,
	EN_MGTIDX_STLCODE_KSCE_RAIL_ASD11,
	EN_MGTIDX_STLCODE_AASHTO_LRFD12,
	EN_MGTIDX_STLCODE_CSA_S6S1_10,
	EN_MGTIDX_STLCODE_EC3_2_05,
	EN_MGTIDX_STLCODE_AISC_LRFD10,
	EN_MGTIDX_STLCODE_AISC_ASD10,
	EN_MGTIDX_STLCODE_SNIP_2_05_03_84,
	EN_MGTIDX_STLCODE_SP_35_13330_2011,
	EN_MGTIDX_STLCODE_SNIP_2_05_03_84_MKS,
	EN_MGTIDX_STLCODE_SP_35_13330_2011_MKS,
	EN_MGTIDX_STLCODE_GB50017_15,
	EN_MGTIDX_STLCODE_AISI_CFSD08,
	EN_MGTIDX_STLCODE_PN_85_S_10030,
	EN_MGTIDX_STLCODE_KSSC_LSD16,
	EN_MGTIDX_STLCODE_KDS_41_31_2019,
	EN_MGTIDX_STLCODE_KBC_LSD16,
	EN_MGTIDX_STLCODE_CSA_S6_14,
	EN_MGTIDX_STLCODE_IRC_6_LSD,
	EN_MGTIDX_STLCODE_IRC_24_2010,
	EN_MGTIDX_STLCODE_AASHTO_LRFD16,
	EN_MGTIDX_STLCODE_GB50017_17,
	EN_MGTIDX_STLCODE_AISC_LRFD16,
	EN_MGTIDX_STLCODE_AISC_ASD16,
	EN_MGTIDX_STLCODE_JTG_D60_15,
	EN_MGTIDX_STLCODE_AASHTO_LRFD17,
	EN_MGTIDX_STLCODE_GB51249_2017,
	EN_MGTIDX_STLCODE_JROAD_H29,
	EN_MGTIDX_STLCODE_NSCP_2015_LRFD,
	EN_MGTIDX_STLCODE_NSCP_2015_ASD,
	EN_MGTIDX_STLCODE_JGJ209_2010,
	EN_MGTIDX_STLCODE_KDS_24_14_30_2019,
	EN_MGTIDX_STLCODE_KDS_41_30_10_2022,
	EN_MGTIDX_STLCODE_KDS_24_14_31_2018,
	EN_MGTIDX_STLCODE_IRS_SBC,
	EN_MGTIDX_STLCODE_AASHTO_LRFD20,
	EN_MGTIDX_STLCODE_JROAD_H24,
	EN_MGTIDX_STLCODE_JROAD_H14,
	EN_MGTIDX_STLCODE_CSA_S6_19,
	EN_MGTIDX_STLCODE_SP_16_13330_2017,
	EN_MGTIDX_STLCODE_AISC_LRFD22,
	EN_MGTIDX_STLCODE_AISC_ASD22,
};

// DB_ST_DT_DN.h¿¡ D_CONC_CODE_???? Á¤ÀÇ Ãß°¡(¼ø¼­ ¹Ù²Ù¸é ¾ÈµÊ)
/// [ CON : Concrete Design ]
#define CONCODE_AASHTO_LFD96         _T("AASHTO-LFD96")
#define CONCODE_AASHTO_LRFD02        _T("AASHTO-LRFD02")
#define CONCODE_AASHTO_LRFD07        _T("AASHTO-LRFD07")
#define CONCODE_AASHTO_LRFD12        _T("AASHTO-LRFD12")
#define CONCODE_AASHTO_LRFD14        _T("AASHTO-LRFD14")
#define CONCODE_AASHTO_LRFD16        _T("AASHTO-LRFD16")
#define CONCODE_AASHTO_LRFD17        _T("AASHTO-LRFD17")
#define CONCODE_AASHTO_LRFD20        _T("AASHTO-LRFD20")
#define CONCODE_AASHTO_STD2K         _T("AASHTO-Std2K")
#define CONCODE_ACI318_02            _T("ACI318-02")
#define CONCODE_ACI318_05            _T("ACI318-05")
#define CONCODE_ACI318_08            _T("ACI318-08")
#define CONCODE_ACI318_11            _T("ACI318-11")
#define CONCODE_ACI318_14            _T("ACI318-14")
#define CONCODE_ACI318_19            _T("ACI318-19")
#define CONCODE_ACI318_25            _T("ACI318-25")
#define CONCODE_ACI318_89            _T("ACI318-89")
#define CONCODE_ACI318_95            _T("ACI318-95")
#define CONCODE_ACI318_99            _T("ACI318-99")
#define CONCODE_ACI318M_14           _T("ACI318M-14")
#define CONCODE_ACI318M_19           _T("ACI318M-19")
#define CONCODE_ACI318M_25           _T("ACI318M-25")
#define CONCODE_AIJ_WSD99            _T("AIJ-WSD99")
#define CONCODE_AIK_USD94            _T("AIK-USD94")
#define CONCODE_AIK_WSD2K            _T("AIK-WSD2K")
#define CONCODE_AS5100_2_17          _T("AS 5100.2:17")
#define CONCODE_AS5100_5_17          _T("AS 5100.5:17")
#define CONCODE_BS5400               _T("BS 5400")
#define CONCODE_BS5400_90            _T("BS 5400-4:1990")
#define CONCODE_TMH07_89            _T("TMH07-3:1989")
#define CONCODE_BS8110_97            _T("BS8110-97")
#define CONCODE_CJJ11_2011           _T("CJJ11-2011") //add CJJ11-2011 by maxiao 2012-3-1
#define CONCODE_CJJ11_2019           _T("CJJ11-2019")
#define CONCODE_CJJ166_2011          _T("CJJ166-2011")
#define CONCODE_CJJ77_98             _T("CJJ77-98")
#define CONCODE_CSA_A23_3_94         _T("CSA-A23.3-94")
#define CONCODE_CSA_S6_00            _T("CSA-S6-00")
#define CONCODE_CSA_S6_14            _T("CSA-S6-14")
#define CONCODE_CSA_S6_19            _T("CSA-S6-19")
#define CONCODE_CSA_S6S1_10          _T("CSA-S6S1-10")
#define CONCODE_EC0                  _T("Eurocode 0")
#define CONCODE_EC2                  _T("Eurocode2")
#define CONCODE_EC2_04               _T("Eurocode2:04")
#define CONCODE_EC2_2_05             _T("Eurocode2-2:05")
#define CONCODE_ESCGB19              _LS(IDS_DB_LCOM_CODE_ENGNEERINGSTRUCTURECOMMONCODE_GB2019)
#define CONCODE_GB50010_02           _T("GB50010-02")
#define CONCODE_GB50010_10           _T("GB/T50010-10")
#define CONCODE_GB50010_19           _T("GB50010-19")
#define CONCODE_GB50069_2002         _T("GB50069-2002")
#define CONCODE_IRC112_2011          _T("IRC:112-2011")
#define CONCODE_IRC112_2020          _T("IRC:112-2020")
#define CONCODE_IRC21_2000           _T("IRC:21-2000")
#define CONCODE_IRC6_2000            _T("IRC:6-2000")
#define CONCODE_IRC6_LSD             _T("IRC:6 LSD") //Pinakin IRC6LSD
#define CONCODE_IRS                  _T("IRS") 
#define CONCODE_IS456_2000           _T("IS456:2000")
#define CONCODE_JROAD_H14            _T("Japan Road III-H14")  // JSCE02¿¡¼­ º¯°æ 
#define CONCODE_JROAD_H14_H24        _T("Japan Road III-H14/H24")
#define CONCODE_JROAD_H29            _T("Japan Road III-H29")  // JSCE17¿¡¼­ º¯°æ
#define CONCODE_JTG_B02_01_2008      _T("JTG/B02-01-2008")
#define CONCODE_JTG_D60_04           _T("JTG D60-04")
#define CONCODE_JTG_D60_15           _T("JTG D60-15")
#define CONCODE_JTG_D62_04           _T("JTG D62-04")
#define CONCODE_JTGT2231_01_2020     _T("JTG/T 2231-01-2020")
#define CONCODE_JTJ021_89            _T("JTJ021-89")
#define CONCODE_JTJ023_85            _T("JTJ023-85")
#define CONCODE_KBC_USD05            _T("KBC-USD05")
#define CONCODE_KBC_USD09            _T("KBC-USD09")
#define CONCODE_KBC_USD16            _T("KBC-USD16")
#define CONCODE_KCI_USD03            _T("KCI-USD03")
#define CONCODE_KCI_USD07            _T("KCI-USD07")
#define CONCODE_KCI_USD12            _T("KCI-USD12")
#define CONCODE_KCI_USD99            _T("KCI-USD99")
#define CONCODE_KDS_24_14_21_2022    _T("KDS 24 14 21 : 2021")
#define CONCODE_KDS_41_20_2022       _T("KDS 41 20 : 2022")
#define CONCODE_KDS_41_30_2018       _T("KDS 41 30 : 2018")
#define CONCODE_KRTA_BRG2K           _T("KRTA-BRG2K")
#define CONCODE_KSCE_LSD15           _T("KSCE-LSD15")
#define CONCODE_KSCE_RAIL_USD04      _T("KSCE-RAIL-USD04")
#define CONCODE_KSCE_RAIL_USD11      _T("KSCE-RAIL-USD11")
#define CONCODE_KSCE_USD03           _T("KSCE-USD03")
#define CONCODE_KSCE_USD05           _T("KSCE-USD05")
#define CONCODE_KSCE_USD10           _T("KSCE-USD10")
#define CONCODE_KSCE_USD96           _T("KSCE-USD96")
#define CONCODE_NSCP_2015            _T("NSCP 2015")
#define CONCODE_NSR_10               _T("NSR-10")
#define CONCODE_PN_85_S_10030        _T("PN-85/S-10030")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define CONCODE_SNIP_2_05_03_84      _T("¬³¬¯¬Ú¬± 2.05.03-84*")
//	#define CONCODE_SNIP_2_05_03_84_MKS  _T("¬³¬¯¬Ú¬± 2.05.03-84*(MKS)")
//	#define CONCODE_SP_35_13330_2011     _T("¬³¬± 35.13330.2011")
//	#define CONCODE_SP_35_13330_2011_MKS _T("¬³¬± 35.13330.2011(MKS)")
//	#define CONCODE_SP_63_13330_2018     _T("¬³¬± 63.13330.2018")
//#else
	#define CONCODE_SNIP_2_05_03_84      _T("SNiP 2.05.03-84*")
	#define CONCODE_SNIP_2_05_03_84_MKS  _T("SNiP 2.05.03-84*(MKS)")
	#define CONCODE_SP_35_13330_2011     _T("SP 35.13330.2011")
	#define CONCODE_SP_35_13330_2011_MKS _T("SP 35.13330.2011(MKS)")
	#define CONCODE_SP_63_13330_2018     _T("SP 63.13330.2018")
//#endif
#define CONCODE_TAIWAN               _T("Taiwan")
#define CONCODE_TB10002_1_05         _T("TB 10002.1-05")
#define CONCODE_TB10002_2017         _T("TB 10002-2017")
#define CONCODE_TB10002_3_05         _T("TB 10002.3-05")
#define CONCODE_TWN_BRG_LSD90        _T("TWN-BRG-LSD90")
#define CONCODE_TWN_USD100           _T("TWN-USD100")
#define CONCODE_TWN_USD112           _T("TWN-USD112")
#define CONCODE_TWN_USD92            _T("TWN-USD92")
#define CONCODE_NTC_DCEC_2017        _T("NTC-DCEC(2017)")
#define CONCODE_NTC_DCEC_2023        _T("NTC-DCEC(2023)")
#define CONCODE_TMH07_19881          _T("TMH07-1981") 
#define CONCODE_AREMA_2023           _T("AREMA-2023")


enum EN_MGTIDX_CONCODE
{
	EN_MGTIDX_CONCODE_NONE = 0,
	EN_MGTIDX_CONCODE_ACI318_89,
	EN_MGTIDX_CONCODE_ACI318_95,
	EN_MGTIDX_CONCODE_ACI318_99,
	EN_MGTIDX_CONCODE_AIK_USD94,
	EN_MGTIDX_CONCODE_KSCE_USD96,
	EN_MGTIDX_CONCODE_KCI_USD99,
	EN_MGTIDX_CONCODE_AIK_WSD2K,
	EN_MGTIDX_CONCODE_AIJ_WSD99,
	EN_MGTIDX_CONCODE_BS8110_97,
	EN_MGTIDX_CONCODE_EC2,
	EN_MGTIDX_CONCODE_GB50010_02,
	EN_MGTIDX_CONCODE_KRTA_BRG2K,
	EN_MGTIDX_CONCODE_JTJ021_89,
	EN_MGTIDX_CONCODE_CJJ77_98,
	EN_MGTIDX_CONCODE_AASHTO_STD2K,
	EN_MGTIDX_CONCODE_JTJ023_85,
	EN_MGTIDX_CONCODE_AASHTO_LRFD02,
	EN_MGTIDX_CONCODE_ACI318_02,
	EN_MGTIDX_CONCODE_CSA_A23_3_94,
	EN_MGTIDX_CONCODE_CSA_S6_00,
	EN_MGTIDX_CONCODE_IRC21_2000,
	EN_MGTIDX_CONCODE_IS456_2000,
	EN_MGTIDX_CONCODE_IRC6_2000,
	EN_MGTIDX_CONCODE_TAIWAN,
	EN_MGTIDX_CONCODE_TWN_BRG_LSD90,
	EN_MGTIDX_CONCODE_AASHTO_LFD96,
	EN_MGTIDX_CONCODE_TWN_USD92,
	EN_MGTIDX_CONCODE_JROAD_H14,
	EN_MGTIDX_CONCODE_JROAD_H29,
	EN_MGTIDX_CONCODE_KSCE_USD03,
	EN_MGTIDX_CONCODE_JTG_D60_04,
	EN_MGTIDX_CONCODE_JTG_D62_04,
	EN_MGTIDX_CONCODE_KSCE_USD05,
	EN_MGTIDX_CONCODE_KSCE_RAIL_USD04,
	EN_MGTIDX_CONCODE_KBC_USD05,
	EN_MGTIDX_CONCODE_KCI_USD03,
	EN_MGTIDX_CONCODE_TB10002_3_05,
	EN_MGTIDX_CONCODE_TB10002_1_05,
	EN_MGTIDX_CONCODE_EC2_04,
	EN_MGTIDX_CONCODE_ACI318_05,
	EN_MGTIDX_CONCODE_KCI_USD07,
	EN_MGTIDX_CONCODE_KBC_USD09,
	EN_MGTIDX_CONCODE_AASHTO_LRFD07,
	EN_MGTIDX_CONCODE_JTG_B02_01_2008,
	EN_MGTIDX_CONCODE_EC2_2_05,
	EN_MGTIDX_CONCODE_EC0,
	EN_MGTIDX_CONCODE_BS5400_90,
	EN_MGTIDX_CONCODE_KSCE_LSD15,
	EN_MGTIDX_CONCODE_KCI_USD12,
	EN_MGTIDX_CONCODE_TWN_USD100,
	EN_MGTIDX_CONCODE_TWN_USD112,
	EN_MGTIDX_CONCODE_GB50010_10,
	EN_MGTIDX_CONCODE_GB50010_19,
	EN_MGTIDX_CONCODE_KSCE_USD10,
	EN_MGTIDX_CONCODE_KSCE_RAIL_USD11,
	EN_MGTIDX_CONCODE_CJJ11_2011,
	EN_MGTIDX_CONCODE_CJJ11_2019,
	EN_MGTIDX_CONCODE_ACI318_08,
	EN_MGTIDX_CONCODE_ACI318_11,
	EN_MGTIDX_CONCODE_AASHTO_LRFD12,
	EN_MGTIDX_CONCODE_CJJ166_2011,
	EN_MGTIDX_CONCODE_CSA_S6S1_10,
	EN_MGTIDX_CONCODE_SNIP_2_05_03_84,
	EN_MGTIDX_CONCODE_SP_35_13330_2011,
	EN_MGTIDX_CONCODE_SNIP_2_05_03_84_MKS,
	EN_MGTIDX_CONCODE_SP_35_13330_2011_MKS,
	EN_MGTIDX_CONCODE_IRC6_LSD,
	EN_MGTIDX_CONCODE_IRC112_2011,
	EN_MGTIDX_CONCODE_NSR_10,
	EN_MGTIDX_CONCODE_AASHTO_LRFD14,
	EN_MGTIDX_CONCODE_JTG_D60_15,
	EN_MGTIDX_CONCODE_ESCGB19,
	EN_MGTIDX_CONCODE_PN_85_S_10030,
	EN_MGTIDX_CONCODE_KDS_41_20_2022,
	EN_MGTIDX_CONCODE_KDS_41_30_2018,    
	EN_MGTIDX_CONCODE_KBC_USD16,
	EN_MGTIDX_CONCODE_CSA_S6_14,
	EN_MGTIDX_CONCODE_ACI318_14,
	EN_MGTIDX_CONCODE_ACI318M_14,
	EN_MGTIDX_CONCODE_AASHTO_LRFD16,
	EN_MGTIDX_CONCODE_GB50069_2002,
	EN_MGTIDX_CONCODE_AS5100_5_17,
	EN_MGTIDX_CONCODE_TB10002_2017,
	EN_MGTIDX_CONCODE_AS5100_2_17,
	EN_MGTIDX_CONCODE_IRS,
	EN_MGTIDX_CONCODE_AASHTO_LRFD17,
	EN_MGTIDX_CONCODE_BS5400,
	EN_MGTIDX_CONCODE_JTGT2231_01_2020,
	EN_MGTIDX_CONCODE_NSCP_2015,
	EN_MGTIDX_CONCODE_ACI318_19,
	EN_MGTIDX_CONCODE_ACI318M_19,
	EN_MGTIDX_CONCODE_KDS_24_14_21_2022,
	EN_MGTIDX_CONCODE_IRC112_2020,
	EN_MGTIDX_CONCODE_NTC_DCEC_2017,
	EN_MGTIDX_CONCODE_AASHTO_LRFD20,
	EN_MGTIDX_CONCODE_CSA_S6_19,
	EN_MGTIDX_CONCODE_SP_63_13330_2018,
	EN_MGTIDX_CONCODE_NTC_DCEC_2023,
	EN_MGTIDX_CONCODE_AREMA_2023,
	EN_MGTIDX_CONCODE_ACI318_25,
	EN_MGTIDX_CONCODE_ACI318M_25,
};

// ¾Æ·¡ Ãß°¡, ¼öÁ¤ ¹× º¯°æ»çÇ×ÀÌ ÀÖÀ¸¸é ÀÀ¿ë±â¼ú1ÆÀ DB´ã´çÀÚ¿¡°Ô ¹Ýµå½Ã ¾Ë¸±°Í.
/// [ SRC Design ]
#define SRCCODE_AIJ_SRC01            _T("AIJ-SRC01")
#define SRCCODE_AIK_SRC2K            _T("AIK-SRC2K")
#define SRCCODE_GB50068_2019		 _T("GB50068-2019")
#define SRCCODE_JGJ138_01            _T("JGJ138-01")
#define SRCCODE_KBC_SRC05            _T("KBC-SRC05")
#define SRCCODE_KBC_SRC09            _T("KBC-SRC09")
#define SRCCODE_KBC_SRC16            _T("KBC-SRC16")
#define SRCCODE_KDS_41_SRC_2019      _T("KDS 41 SRC : 2019")
#define SRCCODE_KDS_41_SRC_2022      _T("KDS 41 SRC : 2022")
#define SRCCODE_SSRC79               _T("SSRC79")
#define SRCCODE_TWN_SRC100           _T("TWN-SRC100")
#define SRCCODE_TWN_SRC92            _T("TWN-SRC92")

enum EN_MGTIDX_SRCCODE
{
	EN_MGTIDX_SRCCODE_NONE = 0,
	EN_MGTIDX_SRCCODE_SSRC79,
	EN_MGTIDX_SRCCODE_AIK_SRC2K,
	EN_MGTIDX_SRCCODE_AIJ_SRC01,
	EN_MGTIDX_SRCCODE_JGJ138_01,
	EN_MGTIDX_SRCCODE_TWN_SRC92,
	EN_MGTIDX_SRCCODE_KBC_SRC05,
	EN_MGTIDX_SRCCODE_TWN_SRC100,
	EN_MGTIDX_SRCCODE_KBC_SRC09,
	EN_MGTIDX_SRCCODE_KBC_SRC16,
	EN_MGTIDX_SRCCODE_KDS_41_SRC_2019,
	EN_MGTIDX_SRCCODE_GB50068_2019,
	EN_MGTIDX_SRCCODE_KDS_41_SRC_2022,
};

/// [ CSG : Composite Steel Girder Design ]
#define CSGCODE_AASHTO_LRFD07        _T("AASHTO-LRFD07")
#define CSGCODE_AASHTO_LRFD12        _T("AASHTO-LRFD12")
#define CSGCODE_AASHTO_LRFD16        _T("AASHTO-LRFD16")
#define CSGCODE_AASHTO_LRFD17        _T("AASHTO-LRFD17")
#define CSGCODE_AASHTO_LRFD20        _T("AASHTO-LRFD20")

#define CSGCODE_CS457_R1             _T("CS457/R1")
#define CSGCODE_CSA_S6_10            _T("CSA-S6-10")
#define CSGCODE_CSA_S6_14            _T("CSA-S6-14")
#define CSGCODE_EN1994_2             _T("EN 1994-2")
#define CSGCODE_IRC22_2008           _T("IRC:22-2008")
#define CSGCODE_IRC22_2015           _T("IRC:22-2015")
#define CSGCODE_JTG_D60_15           _T("JTG D60-15")
#define CSGCODE_KSCE_ASD10           _T("KSCE-ASD10")
#define CSGCODE_KSCE_LSD15           _T("KSCE-LSD15")
#define CSGCODE_KSCE_RAIL_ASD11      _T("KSCE-RAIL-ASD11")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define CSGCODE_SNIP_2_05_03_84      _T("¬³¬¯¬Ú¬± 2.05.03-84*")
//	#define CSGCODE_SP_35_13330_2011     _T("¬³¬± 35.13330.2011")
//#else
	#define CSGCODE_SNIP_2_05_03_84      _T("SNiP 2.05.03-84*")
	#define CSGCODE_SP_35_13330_2011     _T("SP 35.13330.2011")
//#endif
#define CSGCODE_KDS_24_14_31_2018    _T("KDS 24 14 31 : 2018")
#define CSGCODE_AS5100_2_17          _T("AS 5100.2:17")
#define CSGCODE_AS5100_6_2017        _T("AS 5100.6:2017")
#define CSGCODE_CSA_S6_19            _T("CSA-S6-19")

/// [ SOD : Steel Orthotropic Deck Design ]
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define SODCODE_SNIP_2_05_03_84      _T("¬³¬¯¬Ú¬± 2.05.03-84*")
//	#define SODCODE_SP_35_13330_2011     _T("¬³¬± 35.13330.2011")
//#else
	#define SODCODE_SNIP_2_05_03_84      _T("SNiP 2.05.03-84*")
	#define SODCODE_SP_35_13330_2011     _T("SP 35.13330.2011")
//#endif


/// [ STLRAT : Steel Rating Design ] 
#define STLRATCODE_AASHTO_LRFR11    _T("AASHTO-LRFR11")
#define STLRATCODE_AASHTO_LRFR19    _T("AASHTO-LRFR19")
#define STLRATCODE_CS454_20      	_T("CS454/20")
#define STLRATCODE_NR_GN_CIV_025_06 _T("NR/GN/CIV/025:06")
#define STLRATCODE_KSCE_ASD10       _T("KSCE-ASD10")
#define STLRATCODE_KSCE_LSD15		_T("KSCE-LSD15")
#define STLRATCODE_KSCE_RAIL_ASD11  _T("KSCE-RAIL-ASD11")

/// [ CONRAT : Concrete Rating Design ] 
#define CONRATCODE_KSCE_LSD15       _T("KSCE-LSD15")
#define CONRATCODE_KSCE_RAIL_USD11  _T("KSCE-RAIL-USD11")
#define CONRATCODE_KSCE_USD10       _T("KSCE-USD10")

/// [ PSCRAT : PSC Rating Design ] 
#define PSCRATCODE_AASHTO_LRFD05    _T("AASHTO-LRFD05")
#define PSCRATCODE_AASHTO_LRFR11    _T("AASHTO-LRFR11")
#define PSCRATCODE_AASHTO_LRFR19    _T("AASHTO-LRFR19")
#define PSCRATCODE_CS454_20      	_T("CS454/20")
#define PSCRATCODE_KSCE_LSD15		_T("KSCE-LSD15")
#define PSCRATCODE_KSCE_RAIL_USD11  _T("KSCE-RAIL-USD11")
#define PSCRATCODE_KSCE_USD05       _T("KSCE-USD05")
#define PSCRATCODE_KSCE_USD10       _T("KSCE-USD10")

/// [ ALU : Aluminum Design ]
#define ALUCODE_AA_ASD05            _T("AA-ASD05")
#define ALUCODE_AA_ASD10            _T("AA-ASD10") // 10Àº ¾ÆÁ÷ Á¤½ÄÀ¸·Î ¿­¸®Áö´Â ¾ÊÀº »óÅÂ.   
#define ALUCODE_AA_LRFD05           _T("AA-LRFD05")
#define ALUCODE_AA_LRFD10           _T("AA-LRFD10")
#define ALUCODE_GB50429_2007        _T("GB50429-2007")

/// [ BRDGSE : Bridge Seismic Evaluation ]
#define BRDGSE_KEC_2012             _T("KEC2012")
#define BRDGSE_KISTEC_2015          _T("KISTEC2015")
#define BRDGSE_KISTEC_2019          _T("KISTEC2019")
#define BRDGSE_KALIS_2023           _T("KALIS2023")

// [ Uniform standards for reliability design of building structures ]
#define STANDARDCODE_GB50068_2018	_T("GB50068-2018")	//Add by tss(2019.06.05)

#define LCOMCODE_NTC_CDE_2017 _T("NTC-CDE(2017)")
#define LCOMCODE_SP_20_13330_2016	_T("SP 20.13330.2016")
#define LCOMCODE_THAILAND_2021 _T("Thailand(2021)")

#pragma region /// [ MATL CODE - STEEL ]

#define MATLCODE_STL_KS             _T("KS(S)")
#define MATLCODE_STL_KS08           _T("KS08(S)")
#define MATLCODE_STL_KS09           _T("KS09(S)")
#define MATLCODE_STL_KS08_CIVIL     _T("KS08-Civil(S)")
#define MATLCODE_STL_KS_CIVIL       _T("KS-Civil(S)")
#define MATLCODE_STL_ASTM           _T("ASTM(S)")
#define MATLCODE_STL_ASTM09         _T("ASTM09(S)")
#define MATLCODE_STL_JIS            _T("JIS(S)")
#define MATLCODE_STL_JIS_CIVIL      _T("JIS-Civil(S)")
#define MATLCODE_STL_BS             _T("BS(S)")
#define MATLCODE_STL_DIN            _T("DIN(S)")
#define MATLCODE_STL_EN             _T("EN(S)")
#define MATLCODE_STL_UNI            _T("UNI(S)")
#define MATLCODE_STL_GB03           _T("GB03(S)")
#define MATLCODE_STL_GB             _T("GB(S)")
#define MATLCODE_STL_JGJ            _T("JGJ(S)")
#define MATLCODE_STL_JTJ            _T("JTJ(S)")
#define MATLCODE_STL_JTG04          _T("JTG04(S)")
#define MATLCODE_STL_CSA            _T("CSA(S)")
#define MATLCODE_STL_IS             _T("IS(S)")
#define MATLCODE_STL_CNS            _T("CNS(S)")
#define MATLCODE_STL_CNS06          _T("CNS06(S)")
#define MATLCODE_STL_BS04           _T("BS04(S)")
#define MATLCODE_STL_EN05           _T("EN05(S)")
#define MATLCODE_STL_TB05           _T("TB05(S)")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define MATLCODE_STL_GOST_SP       _T("¬³¬±35.2011(¬³¬ä)")
//#else
	#define MATLCODE_STL_GOST_SP       _T("GOST-SP(S)")
//#endif
#define MATLCODE_STL_KSCE_LSD15     _T("KSCE-LSD15(S)")
#define MATLCODE_STL_KS10_CIVIL     _T("KS10-Civil(S)")
#define MATLCODE_STL_EN05_PS        _T("EN05-PS(S)")
#define MATLCODE_STL_EN05_SW        _T("EN05-SW(S)")
#define MATLCODE_STL_GB12           _T("GB12(S)")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define MATLCODE_STL_GOST_SNIP     _T("¬³¬¯¬Ú¬± 2.05.03-84*(¬³¬ä)")
//#else
	#define MATLCODE_STL_GOST_SNIP     _T("GOST-SNIP(S)")
//#endif
#define MATLCODE_STL_BC1_12_ASTM    _T("BC1:12-ASTM(S)")
#define MATLCODE_STL_BC1_12_BSEN    _T("BC1:12-BS EN(S)")
#define MATLCODE_STL_BC1_12_JIS     _T("BC1:12-JIS(S)")
#define MATLCODE_STL_BC1_12_GB      _T("BC1:12-GB(S)")
#define MATLCODE_STL_BC1_12_CLASS2  _T("BC1:12-Class2(S)")
#define MATLCODE_STL_BC1_12_CLASS3  _T("BC1:12-Class3(S)")
#define MATLCODE_STL_JTG3362_18     _T("JTG3362-18(S)")
#define MATLCODE_STL_EN10326        _T("EN10326(S)")
#define MATLCODE_STL_EN10149_2      _T("EN10149-2(S)")
#define MATLCODE_STL_EN10149_3      _T("EN10149-3(S)")
#define MATLCODE_STL_KS16           _T("KS16(S)")
#define MATLCODE_STL_JTG_D64_2015   _T("JTG D64-2015(S)")
#define MATLCODE_STL_GB50917_13     _T("GB 50917-13(S)")
#define MATLCODE_STL_GB50018_02     _T("GB50018-02(S)")
#define MATLCODE_STL_GB50018_25     _T("GB/T50018-25(S)")
#define MATLCODE_STL_JGJ2015        _T("JGJ2015(S)")
#define MATLCODE_STL_KS18           _T("KS18(S)")
#define MATLCODE_STL_GB50017_17     _T("GB50017-17(S)")
#define MATLCODE_STL_TB10092_17     _T("TB10092-17(S)")
#define MATLCODE_STL_TB10091_17     _T("TB10091-17(S)")
#define MATLCODE_STL_AS_NZS_3678    _T("AS/NZS 3678(S)")
#define MATLCODE_STL_AS_NZS_3679_1  _T("AS/NZS 3679.1(S)")
#define MATLCODE_STL_AS_NZS_4672_1  _T("AS/NZS 4672.1(S)")
#define MATLCODE_STL_GB19           _T("GB19(S)")
#define MATLCODE_STL_Q_CR9300_18    _T("Q/CR 9300-18(S)")
#define MATLCODE_STL_CJJ11_2019     _T("CJJ11-2019(S)")
#define MATLCODE_STL_KS22           _T("KS22(S)")
#define MATLCODE_STL_JTJ023_85      _T("JTJ023-85(S)")
#define MATLCODE_STL_TIS1228_2018   _T("TIS 1228-2018(S)")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define MATLCODE_STL_SP16_2017_TB3 _T("¬³¬±16.2017¬ä.¬£3(¬³¬ä)")
//	#define MATLCODE_STL_SP16_2017_TB4 _T("¬³¬±16.2017¬ä.¬£4(¬³¬ä)")
//	#define MATLCODE_STL_SP16_2017_TB5 _T("¬³¬±16.2017¬ä.¬£5(¬³¬ä)")
//#else
	#define MATLCODE_STL_SP16_2017_TB3 _T("SP16.2017t.B3(S)")
	#define MATLCODE_STL_SP16_2017_TB4 _T("SP16.2017t.B4(S)")
	#define MATLCODE_STL_SP16_2017_TB5 _T("SP16.2017t.B5(S)")
//#endif
#define MATLCODE_STL_NR_GN_CIV_025  _T("NR/GN/CIV/025(S)")
#define MATLCODE_STL_ASTM_A416	   _T("ASTM A416")
#define MATLCODE_STL_GB_T_5224	   _T("GB/T 5224")
#define MATLCODE_STL_ETC		   _T("ETC")
#define MATLCODE_STL_KS_D_7002	   _T("KS D 7002")
#define MATLCODE_STL_EN_10138_3	   _T("EN 10138-3")

#pragma endregion

#pragma region /// [ MATL CODE - CONCRETE AND REBARS ]

#define MATLCODE_CON_AS17        _T("AS17(RC)")
#define MATLCODE_CON_ASTM        _T("ASTM(RC)")
#define MATLCODE_CON_ASTM19      _T("ASTM19(RC)")
#define MATLCODE_CON_ASTM19_CVL  _T("ASTM19-Civil(RC)")  // Material Ãß°¡ ÇÏÁö ¾Ê¾ÒÀ½, °­ÇÕ¼º ¼³°è °è»ê¿ë
#define MATLCODE_CON_BS          _T("BS(RC)")
#define MATLCODE_CON_CJJ11_2019  _T("CJJ11-2019(RC)")
#define MATLCODE_CON_CNS         _T("CNS(RC)")
#define MATLCODE_CON_CNS560      _T("CNS560(RC)")
#define MATLCODE_CON_CNS560_18   _T("CNS560-18(RC)")
#define MATLCODE_CON_CSA         _T("CSA(RC)")
#define MATLCODE_CON_EN          _T("EN(RC)")
#define MATLCODE_CON_EN04        _T("EN04(RC)")
#define MATLCODE_CON_GB          _T("GB(RC)")
#define MATLCODE_CON_GB_CIVIL    _T("GB-Civil(RC)")
#define MATLCODE_CON_GB10        _T("GB/T10(RC)")
#define MATLCODE_CON_GB19        _T("GB19(RC)")
#define MATLCODE_CON_GB50917_13  _T("GB 50917-13(RC)")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define MATLCODE_CON_GOST_SNIP       _T("¬³¬¯¬Ú¬± 2.05.03-84*(¬¢)")
//	#define MATLCODE_CON_GOST_SP         _T("¬³¬±35.2011(¬¢)")
//#else
	#define MATLCODE_CON_GOST_SNIP       _T("GOST-SNIP(RC)")
	#define MATLCODE_CON_GOST_SP         _T("GOST-SP(RC)")
//#endif
#define MATLCODE_CON_IRC         _T("IRC(RC)")
#define MATLCODE_CON_IRS         _T("IRS(RC)")
#define MATLCODE_CON_IS          _T("IS(RC)")
#define MATLCODE_CON_JIS         _T("JIS(RC)")
#define MATLCODE_CON_JIS_CIVIL   _T("JIS-Civil(RC)")
#define MATLCODE_CON_JTJ023_85   _T("JTJ023-85(RC)")
#define MATLCODE_CON_JTG04       _T("JTG04(RC)")
#define MATLCODE_CON_JTG3362_18  _T("JTG3362-18(RC)")
#define MATLCODE_CON_KS          _T("KS(RC)")
#define MATLCODE_CON_KS_CIVIL    _T("KS-Civil(RC)")
#define MATLCODE_CON_KS01        _T("KS01(RC)")
#define MATLCODE_CON_KS01_CIVIL  _T("KS01-Civil(RC)")
#define MATLCODE_CON_KS19        _T("KS19(RC)")
#define MATLCODE_CON_KSCE_LSD15  _T("KSCE-LSD15(RC)")
#define MATLCODE_CON_NTC08       _T("NTC08(RC)")
#define MATLCODE_CON_NTC12       _T("NTC12(RC)")
#define MATLCODE_CON_NTC18       _T("NTC18(RC)")
#define MATLCODE_CON_PNS49       _T("PNS49(RC)")
#define MATLCODE_CON_Q_CR9300_18 _T("Q/CR 9300-18(RC)")
#define MATLCODE_CON_SNI         _T("SNI(RC)")
#define MATLCODE_CON_SS          _T("SS(RC)")
#define MATLCODE_CON_TB05        _T("TB05(RC)")
#define MATLCODE_CON_TB10092_17  _T("TB10092-17(RC)")
#define MATLCODE_CON_TIS         _T("TIS(RC)")
#define MATLCODE_CON_TIS_MKS     _T("TIS(MKS)(RC)")
#define MATLCODE_CON_UNI         _T("UNI(RC)")
#define MATLCODE_CON_USC_SI      _T("U.S.C(SI)(RC)")
#define MATLCODE_CON_USC_US      _T("U.S.C(US)(RC)")
#define MATLCODE_CON_NMX_NTC2017 _T("NMX NTC-2017(RC)")
#define MATLCODE_CON_TMH7        _T("TMH7(RC)")
#define MATLCODE_CON_TS          _T("TS(RC)")
//#if defined(_CIVIL_RUS_LOCAL) || defined(_MGEN_RUS_LOCAL)
//	#define MATLCODE_CON_SP63_2018       _T("¬³¬±63.2018(¬¢)")
//#else
	#define MATLCODE_CON_SP63_2018       _T("SP63.2018(RC)")
//#endif
#define MATLCODE_CON_NMX_NTC2023 _T("NMX2023(RC)")
#define MATLCODE_CON_NMX_NTC2023_MKS _T("NMX2023(MKS)(RC)")

#define MATLCODE_REBAR_USER  _T("USER")

#pragma endregion

#pragma region /// [ MATL CODE - ALUMINIUM ]

#define MATLCODE_ALU_AA          _T("AA(A)")
#define MATLCODE_ALU_GB50429_07  _T("GB50429-07(A)")
#define MATLCODE_ALU_EC2023      _T("EC2023(A)")

#pragma endregion

#pragma region /// [ MATL CODE - TIMBER ]

#define MATLCODE_TIMBER_EN338    _T("EN 338(T)")
#define MATLCODE_TIMBER_EN14080  _T("EN 14080(T)")

#pragma endregion

#endif // !defined(__DBCODEDEF_H__)