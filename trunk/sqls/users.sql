CREATE DATABASE `users`;

USE `users`;

--
-- Table structure for table `mymoldb_users`
--

DROP TABLE IF EXISTS `mymoldb_users`;
CREATE TABLE `mymoldb_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nick_name` text,
  `user_group` int(11) NOT NULL DEFAULT '2',
  `password` text,
  `email` text,
  `register_date` datetime DEFAULT NULL,
  `status` smallint(6) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `mymoldb_users`
--

LOCK TABLES `mymoldb_users` WRITE;
INSERT INTO `mymoldb_users` VALUES (0,'root',1,'md5sum of your password','your username (emali)','datatime (eg. 2011-12-12 11:24:34)',1);
UNLOCK TABLES;
