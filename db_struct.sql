-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jun 15, 2016 at 10:56 PM
-- Server version: 5.6.30-0ubuntu0.14.04.1
-- PHP Version: 5.6.21-1+donate.sury.org~trusty+4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `alert`
--

-- --------------------------------------------------------

--
-- Table structure for table `alert_pics`
--

CREATE TABLE IF NOT EXISTS `alert_pics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `alert_id` int(11) NOT NULL,
  `path` text NOT NULL,
  `ts` int(11) NOT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1959 ;

-- --------------------------------------------------------

--
-- Table structure for table `alerts`
--

CREATE TABLE IF NOT EXISTS `alerts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `f_ts` int(11) NOT NULL,
  `mid` text NOT NULL,
  `area` text NOT NULL,
  `account` text NOT NULL,
  `rm_string` text NOT NULL,
  `ack` int(11) NOT NULL,
  `ack_ts` int(11) NOT NULL,
  `ack_by` text NOT NULL,
  `del_by` text,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=419 ;

-- --------------------------------------------------------

--
-- Table structure for table `area_state`
--

CREATE TABLE IF NOT EXISTS `area_state` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `area` text NOT NULL,
  `account` text NOT NULL,
  `state` int(11) NOT NULL DEFAULT '0',
  `latitude` double NOT NULL DEFAULT '52.1',
  `longitude` double NOT NULL DEFAULT '10.1',
  `updated` int(11) NOT NULL DEFAULT '0',
  `login` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=50 ;

-- --------------------------------------------------------

--
-- Table structure for table `emergency_update`
--

CREATE TABLE IF NOT EXISTS `emergency_update` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mid` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `history`
--

CREATE TABLE IF NOT EXISTS `history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` int(11) NOT NULL,
  `user` varchar(20) NOT NULL,
  `action` varchar(40) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=7852 ;

-- --------------------------------------------------------

--
-- Table structure for table `m2m`
--

CREATE TABLE IF NOT EXISTS `m2m` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mid` varchar(20) NOT NULL,
  `pw` varchar(20) NOT NULL,
  `last_seen` int(11) NOT NULL DEFAULT '0',
  `last_ip` varchar(15) NOT NULL DEFAULT '0',
  `area` int(40) NOT NULL,
  `account` varchar(40) NOT NULL,
  `alias` text NOT NULL,
  `brightness_pos` int(11) NOT NULL DEFAULT '255',
  `color_pos` int(11) NOT NULL DEFAULT '254',
  `mRed` int(11) NOT NULL DEFAULT '0',
  `mGreen` int(11) NOT NULL DEFAULT '0',
  `mBlue` int(11) NOT NULL DEFAULT '255',
  `alarm_ws` tinyint(1) NOT NULL DEFAULT '1',
  `alarm_while_streaming` tinyint(1) NOT NULL DEFAULT '1',
  `frame_dist` varchar(5) NOT NULL DEFAULT '0.5',
  `resolution` varchar(5) NOT NULL DEFAULT 'HD',
  `v_short` varchar(5) NOT NULL DEFAULT '-',
  `v_hash` varchar(20) NOT NULL DEFAULT '-',
  `external_state` int(11) NOT NULL DEFAULT '0',
  `with_lights` int(11) NOT NULL DEFAULT '1',
  `with_cam` int(11) NOT NULL DEFAULT '1',
  `with_pir` int(11) NOT NULL DEFAULT '1',
  `with_ext` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `id_2` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=64 ;

-- --------------------------------------------------------

--
-- Table structure for table `rules`
--

CREATE TABLE IF NOT EXISTS `rules` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `area` text NOT NULL,
  `account` text NOT NULL,
  `sub_rule` int(1) NOT NULL,
  `conn` text NOT NULL,
  `arg1` text NOT NULL,
  `arg2` text NOT NULL,
  UNIQUE KEY `id_2` (`id`),
  KEY `id` (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=735 ;

-- --------------------------------------------------------

--
-- Table structure for table `ws`
--

CREATE TABLE IF NOT EXISTS `ws` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `login` text NOT NULL,
  `pw` text NOT NULL,
  `location` text,
  `update` int(11) NOT NULL DEFAULT '0',
  `ip` text,
  `account` text NOT NULL,
  `email` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=34 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
