CREATE TABLE `Login`(
    `Employee ID` VARCHAR(255) NOT NULL,
    `Password` VARCHAR(255) NOT NULL,
    `Status` CHAR(255) NOT NULL,
    PRIMARY KEY(`Employee ID`)
);
ALTER TABLE
    `Login` ADD PRIMARY KEY(`Password`);
CREATE TABLE `Level 1 - Staff`(
    `Name` TEXT NOT NULL,
    `Staff ID` VARCHAR(255) NOT NULL,
    `Employee ID` VARCHAR(255) NOT NULL,
    `Contact number` BIGINT NOT NULL,
    `Current Address` TEXT NOT NULL,
    PRIMARY KEY(`Staff ID`)
);
ALTER TABLE
    `Level 1 - Staff` ADD PRIMARY KEY(`Employee ID`);
ALTER TABLE
    `Level 1 - Staff` ADD UNIQUE `level 1 _ staff_contact number_unique`(`Contact number`);
CREATE TABLE `Level 2 - Manager`(
    `Name` TEXT NOT NULL,
    `Manager ID` VARCHAR(255) NOT NULL,
    `Employee ID` VARCHAR(255) NOT NULL,
    `Contact Number` BIGINT NOT NULL,
    `Office Number` BIGINT NOT NULL,
    `Current Address` TEXT NOT NULL,
    PRIMARY KEY(`Manager ID`)
);
ALTER TABLE
    `Level 2 - Manager` ADD PRIMARY KEY(`Employee ID`);
ALTER TABLE
    `Level 2 - Manager` ADD UNIQUE `level 2 _ manager_contact number_unique`(`Contact Number`);
ALTER TABLE
    `Level 2 - Manager` ADD UNIQUE `level 2 _ manager_office number_unique`(`Office Number`);
CREATE TABLE `Level 3 - Boss`(
    `Name` TEXT NOT NULL,
    `Boss ID` VARCHAR(255) NOT NULL,
    `Employee ID` VARCHAR(255) NOT NULL,
    `Current Address` TEXT NOT NULL,
    PRIMARY KEY(`Boss ID`)
);
ALTER TABLE
    `Level 3 - Boss` ADD PRIMARY KEY(`Employee ID`);